import datetime
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from decouple import config
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

LOG_FILE = settings.BASE_DIR / 'deploy.log'
pa_user = config('PA_USERNAME', default=None)

def _log(msg, level='INFO'):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{ts}] [{level}] {msg}\n')


class Command(BaseCommand):
    help = 'Pull latest, install deps, collectstatic, run migrations, reload web'

    def handle(self, *args, **options):
        _log('Deploy iniciado')
        base = settings.BASE_DIR

        steps = [
            ('git pull', self._step_git_pull),
            ('pip install', self._step_pip_install),
            ('collectstatic', self._step_collectstatic),
            ('makemigrations', self._step_makemigrations),
            ('migrate', self._step_migrate),
        ]

        for label, fn in steps:
            self.stdout.write(f'[{label}]...', ending=' ')
            self.stdout.flush()
            try:
                fn(base)
                self.stdout.write(self.style.SUCCESS('OK'))
                _log(f'{label}: OK')
            except Exception as e:
                self.stdout.write(self.style.ERROR('FAIL'))
                self.stderr.write(str(e))
                _log(f'{label}: FAIL\n{e}', 'ERROR')
                sys.exit(1)

        self._reload()
        self.stdout.write(self.style.SUCCESS('Deploy concluído.'))
        _log('Deploy concluído com sucesso')

    def _step_git_pull(self, base):
        subprocess.run(['git', '-C', str(base), 'pull', 'origin', 'main'], check=True, capture_output=True, text=True)

    def _step_pip_install(self, base):
        subprocess.run(['pip', 'install', '-r', f'{base}/requirements.txt'], check=True, capture_output=True, text=True)

    def _step_collectstatic(self, base):
        call_command('collectstatic', interactive=False)

    def _step_makemigrations(self, base):
        call_command('makemigrations')

    def _step_migrate(self, base):
        call_command('migrate')

    def _reload(self):
        pa_token = config('PA_API_TOKEN', default=None)
        if not pa_token or not pa_user:
            self.stdout.write(self.style.WARNING('[reload web app] SKIP (PA_API_TOKEN/PA_USERNAME not set)'))
            _log('reload web app: SKIP (env vars not set)', 'WARNING')
            return
        domain = f'{pa_user}.pythonanywhere.com'
        url = f'https://www.pythonanywhere.com/api/v0/user/{pa_user}/webapps/{domain}/reload/'
        self.stdout.write('[reload web app]...', ending=' ')
        self.stdout.flush()
        try:
            req = Request(url, method='POST', headers={'Authorization': f'Token {pa_token}'})
            with urlopen(req):
                self.stdout.write(self.style.SUCCESS('OK'))
                _log('reload web app: OK')
        except HTTPError as e:
            body = e.read().decode()
            self.stdout.write(self.style.WARNING(f'API {e.code}: {body}'))
            _log(f'reload web app: API {e.code} - {body}', 'WARNING')
        except URLError as e:
            self.stdout.write(self.style.WARNING(f'Connection error: {e.reason}'))
            _log(f'reload web app: connection error - {e.reason}', 'ERROR')
