import argparse
import os
import shutil
import subprocess
import sys
import time
import distutils.dir_util
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Auto2to3EventHandler(FileSystemEventHandler):
    def __init__(self, from_path, dst_path):
        FileSystemEventHandler.__init__(self)
        self.from_path = from_path
        self.dst_path = dst_path

    def register(self, observer):
        observer.schedule(self, path=self.from_path, recursive=True)

    def on_modified(self, event):
        if event.is_directory:
            return

        self.update_file(event.src_path)

    on_created = on_modified

    def update_file(self, src_path):
        print "updating file   %s" % src_path
        rel_path = os.path.relpath(src_path, self.from_path)
        dst_path = os.path.abspath(os.path.join(self.dst_path, rel_path))
        dst_dir = os.path.dirname(dst_path)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        shutil.copy(src_path, dst_path)
        if src_path.endswith('.py'):
            print "converting file %s" % src_path
            subprocess.call(['2to3', '--write', '--nobackups', dst_path])

    def rebuild(self):
        distutils.dir_util.copy_tree(self.from_path, self.dst_path, update=True)
        subprocess.call(['2to3', '--write', '--nobackups', self.dst_path])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Call 2to3 on changed files.')
    parser.add_argument('--rebuild', action='store_true')
    parser.add_argument('--from', dest='from_paths', action='append')
    parser.add_argument('--to', dest='dst_paths', action='append')

    args = parser.parse_args()

    if (not args.from_paths or not args.dst_paths
        or len(args.from_paths) != len(args.dst_paths)):
        parser.print_help()
        sys.exit(1)

    observer = Observer()
    for from_path, dst_path in zip(args.from_paths, args.dst_paths):
        print "converting from %s to %s" % (from_path, dst_path)
        event_handler = Auto2to3EventHandler(from_path, dst_path)
        if args.rebuild:
            print "  rebuilding..."
            event_handler.rebuild()
        event_handler.register(observer)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()