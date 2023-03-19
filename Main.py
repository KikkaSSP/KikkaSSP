# coding=utf-8
import os
import sys
import psutil
import logging
import logging.handlers


def awake(local_server):
    # logging level (low to hight):
    # CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
    file_handler = set_logging(logging.INFO)
    sys.excepthook = handle_exception

    add_search_path()

    # init kikka
    import kikka

    logging.info("sys.path %s" % sys.path)

    # set debug mode
    if '-c' in sys.argv:
        kikka.memory.isDebug = True
        kikka.app.isDebug = True
        kikka.core.isDebug = True
        file_handler.setLevel(logging.DEBUG)

    kikka.app.awake()
    local_server.newConnection.connect(lambda: kikka.core.signal.Show.emit())

    # font = QFont(kikka.path.RESOURCES + "InconsolataGo-Regular.ttf", 10)
    # QApplication.instance().setFont(font)
    pass


def set_logging(level):
    if level == logging.DEBUG or level == logging.NOTSET:
        fmt = '%(asctime)s | line:%(lineno)-4d %(filename)-20s %(funcName)-30s | %(levelname)-8s| %(message)s'
        logging.basicConfig(level=level, format=fmt)
        file_handler = logging.handlers.RotatingFileHandler(
            'kikka.log', mode='w', maxBytes=5.01*1024*1024, backupCount=0, encoding='utf-8')
        formatter = logging.Formatter(fmt)
    else:
        fmt = '%(asctime)s | line:%(lineno)-4d %(filename)-20s | %(levelname)-8s| %(message)s'
        logging.basicConfig(level=level, format=fmt)
        file_handler = logging.handlers.RotatingFileHandler(
            'kikka.log', mode='a', maxBytes=1.01*1024*1024, backupCount=0, encoding='utf-8')
        formatter = logging.Formatter(fmt)

    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    return file_handler


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Run time error\n%s: %s\n%s" % (exc_type.__name__, exc_value, "-" * 40),
                  exc_info=(exc_type, exc_value, exc_traceback))
    logging.info("\n%s\n%s" % ("-" * 120, "-" * 120))


def add_search_path():
    logging.info("sys.path %s" % sys.path)

    root_path = os.path.dirname(os.path.abspath(__file__))
    if root_path in sys.path:
        sys.path.remove(root_path)
    sys.path.insert(0, root_path)

    root_dir = ["Scripts", "Ghosts", "Resources"]
    for dir_ in root_dir:
        p = os.path.join(root_path, dir_)
        if p in sys.path:
            continue
        sys.path.append(p)


def create_local_server():
    from PyQt5.QtNetwork import QLocalSocket, QLocalServer
    serverName = 'Kikka'
    socket = QLocalSocket()
    socket.connectToServer(serverName)
    if socket.waitForConnected(100):
        return None
    else:
        localServer = QLocalServer()
        localServer.setSocketOptions(QLocalServer.WorldAccessOption)
        localServer.listen(serverName)
        return localServer


def run():
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)

        local_server = create_local_server()
        if not local_server:
            app.quit()
            return

        awake(local_server)

        app.exec_()

        local_server.close()
        sys.exit(0)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    run()
