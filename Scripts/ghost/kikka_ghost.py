
import os
import sys
import json
import logging
import importlib

from kikka.helper import Singleton
from kikka.fileloader import FileLoader
from ghost.shell import Shell
from ghost.balloon import Balloon


class KikkaGhost(Singleton):
    isDebug = False

    def __init__(self):
        self._ghosts = []
        self._name2id = {}

        self._ghost_dir = ''

    def scan_ghost(self, ghost_dir):
        if not os.path.exists(ghost_dir):
            logging.warning("ghost dir is NOT exist: %s" % ghost_dir)
            return
        self._ghost_dir = ghost_dir

        gid = 0
        names = []
        for parent, dir_names, file_names in os.walk(ghost_dir):
            li = list(dir_names)
            for file in file_names:
                ext = os.path.splitext(file)[1]
                if ext == '.zip':
                    li.append(file)

            for ghost_name in li:
                ghost_path = os.path.join(parent, ghost_name)
                ghost = self._load_ghost(ghost_path, gid)
                if ghost is None:
                    continue

                if ghost.name in names:
                    logging.warning("%s(%s) load FAIL. name has been exist", ghost.name, ghost_path)
                    continue

                logging.info("add ghost: %s", ghost.name)
                self._ghosts.append(ghost)
                self._name2id[ghost.name] = gid
                names.append(ghost.name)
                gid += 1
        logging.info("ghost scan finish: count %d", len(self._ghosts))

    def _check_ghost_descript(self, ghost_data, file_loader):
        config = ghost_data.get("config", None)
        errlog = "invalid syntax in ghost's descript.json: "
        if config is None:
            logging.info(errlog + "lost key['config']")
            return False

        if not isinstance(config, dict):
            logging.info(errlog + "key['config'] must be dict")
            return False

        if config.get("name", None) is None:
            logging.info(errlog + "lost key['config']['name']")
            return False

        main = config.get("main", None)
        if main is None:
            logging.info(errlog + "lost key['config']['main']")
            return False

        if file_loader.get_fp("Ghost.zip", "r"):
            fl = FileLoader(os.path.join(file_loader.root_path, "Ghost.zip"))
            if not fl.is_initialized or not fl.is_zip or fl.get_fp("%s.pyc" % main, "r"):
                logging.info(errlog + "illegal file key['config']['main']=" + "Ghost.zip")
                return False
        else:
            path = os.path.join("Ghost", main)
            if not file_loader.get_fp(path, "r"):
                logging.info(errlog + "lost file key['config']['main']=" + path)
                return False

        requirements = config.get("requirements", None)
        if requirements:
            if not isinstance(requirements, list):
                logging.info(errlog + "config.requirements must be list")
                return False

        return True

    def _load_ghost(self, ghost_path, ghost_id):
        file_loader = FileLoader(ghost_path)
        if not file_loader.is_initialized:
            return None

        fp = file_loader.get_fp("descript.json", "r")
        if not fp:
            return None

        data = json.load(fp)
        if self._check_ghost_descript(data, file_loader) is False:
            return None

        main = data["config"]["main"]
        main = os.path.splitext(main)[0]
        main = "Ghost.%s" % main

        if file_loader.get_fp("Ghost.zip", "r"):
            ghost_root = os.path.join(file_loader.root_path, "Ghost.zip")
        else:
            ghost_root = file_loader.root_path
        sys.path.append(ghost_root)

        libPath = os.path.join(file_loader.root_path, "Lib")
        if os.path.exists(libPath):
            sys.path.insert(0, libPath)

        try:
            m = importlib.import_module(main)
            ghost = m.createGhost(ghost_id, data, file_loader)
        except ImportError as e:
            logging.info(e.args)
            ghost = None
        finally:
            if os.path.exists(libPath):
                sys.path.remove(libPath)
            sys.path.remove(ghost_root)

        return ghost

    def get_ghost(self, ghost_id):
        if 0 <= ghost_id < len(self._ghosts):
            return self._ghosts[ghost_id]
        else:
            logging.warning("get_ghost: ghost_id=%d NOT in ghost list" % ghost_id)
            return None

    def get_ghost_by_name(self, ghost_name):
        if ghost_name in self._name2id:
            gid = self._ghosts[self._name2id[ghost_name]]
            return self._ghosts[gid]
        else:
            logging.warning("get_ghost_by_name: '%s' NOT in ghost list" % ghost_name)
            return None

    def get_ghost_count(self):
        return len(self._ghosts)

    def scan_shell(self, shell_dir):
        if not os.path.exists(shell_dir):
            logging.warning("shell dir is NOT exist: %s" % shell_dir)
            return [], {}

        sid = 0
        names = {}
        shells = []
        for parent, dir_names, file_names in os.walk(shell_dir):
            li = list(dir_names)
            for file in file_names:
                ext = os.path.splitext(file)[1]
                if ext == '.zip':
                    li.append(file)

            for shell_name in li:
                shell_path = os.path.join(parent, shell_name)
                shell = Shell(shell_path)

                if shell.is_initialized is False:
                    continue

                if shell.name in names:
                    logging.warning("shell %s(%s) load FAIL. name has been exist", shell.name, shell_path)
                    continue

                logging.info("add shell: %s", shell.name)
                shells.append(shell)
                names[shell.name] = sid
                sid += 1

        logging.info("shell scan finish: count %d", len(shells))
        return shells, names

    def scan_balloon(self, balloon_dir):
        if not os.path.exists(balloon_dir):
            logging.warning("balloon dir is NOT exist: %s" % balloon_dir)
            return [], {}

        bid = 0
        names = {}
        balloons = []
        for parent, dir_names, file_names in os.walk(balloon_dir):
            li = list(dir_names)
            for file in file_names:
                ext = os.path.splitext(file)[1]
                if ext == '.zip':
                    li.append(file)

            for balloon_name in li:
                balloon_path = os.path.join(parent, balloon_name)
                balloon = Balloon(balloon_path)

                if balloon.is_initialized is False:
                    continue

                if balloon.name in names:
                    logging.warning("balloon %s(%s) load FAIL. name has been exist", balloon.name, balloon_path)
                    continue

                logging.info("add balloon: %s", balloon.name)
                balloons.append(balloon)
                names[balloon.name] = bid
                bid += 1

        logging.info("balloon count: %d", len(balloons))
        return balloons, names

    def _load_balloon(self, balloon_dict, balloon_path):
        balloon = Balloon(balloon_path)
        if balloon.is_initialized is False:
            return

        is_exist = False
        for name, b in balloon_dict.items():
            if balloon.name == name and balloon.unicode_name == b.unicode_name:
                is_exist = True
                break

        if not is_exist:
            logging.info("scan balloon: %s", balloon.unicode_name)
            balloon_dict[balloon.name] = balloon
        else:
            logging.warning("%s(%s) load FAIL. name has been exist", balloon.unicode_name, balloon_path)
        pass
