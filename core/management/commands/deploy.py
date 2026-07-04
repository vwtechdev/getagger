import subprocess
import sys

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Pull latest, install deps, collectstatic, run migrations'

    def handle(self, *args, **options):
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
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR('FAIL'))
                self.stderr.write(e.stderr or e.stdout)
                sys.exit(1)

        self.stdout.write(self.style.SUCCESS('Deploy concluído.'))
