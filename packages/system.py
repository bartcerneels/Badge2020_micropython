import machine
import settings

def recover_menu():
    print("Recovering menu!")
    try:
        settings.remove('apps.autorun')
    except KeyError:
        # can happen when no apps.autorun is set
        pass
    settings.store()
    machine.reset()

def execute_repl():
    print("Executing REPL!")
    settings.set('apps.autorun', 'apps.repl')
    settings.store()
    machine.reset()

def start(app, status=False):
    settings.set('apps.autorun', app)
    settings.store()
    machine.reset()
