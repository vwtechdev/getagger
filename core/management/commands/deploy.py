import datetime
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from decouple import config
from django.conf import settings
from django.core.management.base import BaseCommand

LOG_FILE = settings.BASE_DIR / 'deploy.log'


def _log(msg, level='INFO'):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f'[{ts}] [{level}] {msg}\n')


class Command(BaseCommand):
    help = 'Pull latest, install deps, collectstatic, run migrations, reload web'

    def handle(self, *args, **options):
        _log('Deploy iniciado')
        base = settings.BASE_DIR
        venv = getattr(settings, 'DEPLOY_VENV_PATH', '/home/getagger/.virtualenvs/venv')
        pip = f'{venv}/bin/pip'
        python = f'{venv}/bin/python'

        cmds = [
            (['git', '-C', str(base), 'pull', 'origin', 'main'], 'git pull'),
            ([pip, 'install', '-r', f'{base}/requirements.txt'], 'pip install'),
            ([python, 'manage.py', 'collectstatic', '--noinput'], 'collectstatic'),
            ([python, 'manage.py', 'makemigrations'], 'makemigrations'),
            ([python, 'manage.py', 'migrate'], 'migrate'),
        ]
        for cmd, label in cmds:
            self.stdout.write(f'[{label}]...', ending=' ')
            self.stdout.flush()
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.stdout.write(self.style.SUCCESS('OK'))
                _log(f'{label}: OK')
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR('FAIL'))
                self.stderr.write(e.stderr or e.stdout)
                _log(f'{label}: FAIL\n{e.stderr or e.stdout}', 'ERROR')
                sys.exit(1)

        self._reload()

        self.stdout.write(self.style.SUCCESS('Deploy concluído.'))
        _log('Deploy concluído com sucesso')

    def _reload(self):
        pa_token = config('PA_API_TOKEN', default=None)
        pa_user = config('PA_USERNAME', default=None)
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
