from django.core import management

from threading import Thread


def threaded_management_command(command, kwargs=None):
    if kwargs is None:
        kwargs = {}
    thread = Thread(target=management.call_command, args=[command], kwargs=kwargs)
    thread.start()
