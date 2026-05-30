import os
import shutil

def remove_pycache(root_dir):
    paths_to_remove = ['__pycache__', 'logs', 'exports', 'Project', 'data']
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for path in paths_to_remove:
            if path in dirnames:
                full_path = os.path.join(dirpath, path)
                shutil.rmtree(full_path)

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    remove_pycache(root)
    print("Done!")


if __name__ == "__main__":
    main()