import os
import shutil
import sys
from invoke import task


class Env:
    activate = None
    python = None

    @classmethod
    def venv_root(cls):
        if cls.activate:
            return cls.activate

        possible = [ '.', '.wsl', '.venv', 'venv' ]
        for x in possible:
            activate = os.path.join(x, 'bin', 'activate')
            if os.path.isfile(activate):
                cls.activate = activate
                return activate

        print(f'You may not have setup a virtual environment,'
              f' please run invoke setup to create one.')
        sys.exit(1)

    @classmethod
    def which_python(cls, ctx):
        if cls.python:
            return cls.python

        possible = [ 'python3.7', 'python3.6', ]
        for x in possible:
            result = ctx.run(f'{x} --version', hide='both')
            if result.exited == 0:
                cls.python = x
                cls.venv_root()
                return

        print(f'We need either python3.6 or python3.7 to continue.')
        sys.exit(1)


def setup_venv(ctx):
    print('setting up virtual environment')
    Env.which_python(ctx)
    ctx.run(f'{Env.python} -m venv .', hide='both')


def upgrade_pip(ctx):
    print('upgrading pip')
    with ctx.prefix(f'source {Env.venv_root()}'):
        ctx.run('pip install -U pip setuptools wheel', hide='both')


def install_requirements(ctx):
    print('installing requirements')
    with ctx.prefix(f'source {Env.venv_root()}'):
        ctx.run('pip install -r requirements.txt', hide='both')


@task
def setup(ctx):
    """Sets up a virtual environment for you"""
    activate = Env.venv_root()
    if not activate:        
        setup_venv(ctx)
    upgrade_pip(ctx)
    install_requirements(ctx)


@task(pre=[ setup ])
def clean(ctx):
    """cleans your dist and build directories"""
    print('cleaning')
    shutil.rmtree('build')
    shutil.rmtree('dist')


@task(pre=[ clean ])
def build(ctx):
    """builds source and binary wheels for deployment"""
    print('building')
    with ctx.prefix(f'source {Env.venv_root()}'):
        ctx.run('python setup.py sdist bdist_wheel', hide='both')


@task(pre=[ build ])
def deploy(ctx):
    """deploys source and binary wheels to pypi"""
    print('deploying')
    with ctx.prefix(f'source {Env.venv_root()}'):
        ctx.run('twine upload dist/*')


@task
def unsetup(ctx):
    """Removes the virtual environment for you"""
    activate = Env.venv_root()
    if activate:
        subdirs = [ 'bin', 'lib', 'include', ]
        dir_name = os.path.dirname(os.path.dirname(activate))
        for x in subdirs:
            x = os.path.join(dir_name, x)
            shutil.rmtree(x)
