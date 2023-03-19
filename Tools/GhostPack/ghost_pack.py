
import os
import json
import shutil
import zipfile
import argparse

DESCRIPT_FILE = "descript.json"


class GhostPack:
    def pack(self, ghost_path, output_path, as_zip=True):
        self.ghost_path = ghost_path
        self.ghost_data = json.load(open(os.path.join(self.ghost_path, DESCRIPT_FILE), "r"))
        self.ghost_name = self.ghost_data.get("config").get("name")
        self.temp_path = os.path.join(self.ghost_path, "temp", self.ghost_name)
        self.lib_path = os.path.join(self.temp_path, "Lib")

        # clear temp
        if os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)
        os.makedirs(self.temp_path)

        # compile ghost
        script_path = os.path.join(self.ghost_path, "Ghost")
        if os.path.isdir(script_path):
            self._compile_ghost(script_path, self.temp_path)

        # install require lib
        requirements = self.ghost_data.get("config").get("requirements", [])
        if requirements:
            os.makedirs(self.lib_path)
            self._install_requirement(requirements, self.lib_path)

        # pack resource
        res_path = os.path.join(self.ghost_path, "Resource")
        if os.path.isdir(res_path):
            self._pack_resource(res_path, os.path.join(self.temp_path, "Resource"))

        # copy others file
        self._copy_file()

        # output
        if as_zip:
            f = zipfile.ZipFile(os.path.join(output_path, "%s.zip" % self.ghost_name), 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(self.temp_path):
                for file in files:
                    dstPath = os.path.join(self.ghost_name, os.path.relpath(root, self.temp_path), file)
                    f.write(os.path.join(root, file), dstPath)
            f.close()
        else:
            shutil.copytree(self.temp_path, os.path.join(output_path, self.ghost_name))

        # clear
        for root, dirs, files in os.walk(script_path):
            for file in files:
                if os.path.splitext(file)[1] in [".pyz", ".pyo", ".pyc", ".pyd"]:
                    os.remove(os.path.join(root, file))
        shutil.rmtree(os.path.join(self.ghost_path, "temp"))

    def _compile_ghost(self, ghost_path, output_path):
        # compile
        cmd = 'py -3.6 -m compileall "%s" -b' % ghost_path
        os.system(cmd)

        # pack
        zip_name = "Ghost.zip"
        f = zipfile.ZipFile(os.path.join(output_path, zip_name), 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(ghost_path):
            if os.path.basename(root) == '__pycache__':
                continue

            for file in files:
                if os.path.splitext(file)[1] not in [".pyz", ".pyo", ".pyc", ".pyd"]:
                    continue
                dstPath = os.path.join("Ghost", os.path.relpath(root, ghost_path), file)
                f.write(os.path.join(root, file), dstPath)
        f.close()

    def _install_requirement(self, requirement_list, output_path):
        print("\n==== install requirement ====================")
        for lib in requirement_list:
            print("install", lib)
            os.system("py -3.6 -m pip install %s --target %s" % (lib, output_path))

    def _pack_dir(self, target_dir, output_path):
        root_path = os.path.abspath(os.path.join(target_dir, ".."))
        dir_name = os.path.basename(target_dir)
        zip_name = dir_name + ".zip"
        print("pack", zip_name)

        f = zipfile.ZipFile(os.path.join(output_path, zip_name), 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                dstPath = os.path.join(os.path.relpath(root, root_path), file)
                f.write(os.path.join(root, file), dstPath)
        f.close()

    def _walk_pack(self, walk_path, output_path):
        os.makedirs(output_path)
        for root, dirs, files in os.walk(walk_path):
            if root != walk_path:
                break
            for dir in dirs:
                self._pack_dir(os.path.join(walk_path, dir), output_path)

    def _pack_resource(self, resource_path, output_path):
        print("\n==== pack resource ====================")
        list_dir = os.listdir(resource_path)
        for dir in list_dir:
            walk_path = os.path.join(resource_path, dir)
            if os.path.isfile(walk_path):
                continue
            self._walk_pack(walk_path, os.path.join(output_path, dir))

    def _copy_file(self):
        # copy DESCRIPT_FILE
        shutil.copy(os.path.join(self.ghost_path, DESCRIPT_FILE), os.path.join(self.temp_path, DESCRIPT_FILE))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', help='ghost path', type=str, required=True)
    parser.add_argument('-o', '--output', help='output path', type=str, default='')
    parser.add_argument('-z', '--zip', help='output zip', action="store_true")

    args = parser.parse_args()
    ghost_path = args.path
    output_path = args.output
    as_zip = args.zip

    if output_path == "":
        output_path = ghost_path

    GhostPack().pack(ghost_path, output_path, as_zip)
