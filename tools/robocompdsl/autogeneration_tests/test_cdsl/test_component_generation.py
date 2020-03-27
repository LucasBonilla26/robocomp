#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import glob
import os
import shutil
import subprocess
import sys
import traceback
from shutil import rmtree

from termcolor import cprint, colored

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TESTS_DIR = os.path.join(CURRENT_DIR)

class MyParser(argparse.ArgumentParser):
    """
    Convenience class for the ArgParse parser.
    """

    def error(self, message):
        cprint('error: %s' % message, 'red')
        self.print_help()
        sys.exit(2)


class ComponentGenerationChecker:
    """
    Class containing methods used to generate code and compile a bunch of components to be tested.
    """

    def __init__(self):
        self.results = {}
        self.valid = 0
        self.generated = 0
        self.compiled = 0
        self.comp_failed = 0
        self.gen_failed = 0
        self.dry_run = False

    def generate_code(self, cdsl_file, log_file, dry_run=True):
        """
        Execution of the robocompdsl script to generate the component code for a gigen .cdsl file.
        :param cdsl_file: filename of the .cdsl of the component to be generated
        :param log_file: name of the log file to be written with the result of the command execution.
        :param dry_run: Force to just show messages of what would be done but no command is executed.
        :return: command execution return code
        """
        robocompdsl_exe = shutil.which("robocompdsl")
        if not robocompdsl_exe:
            if os.path.isfile("/opt/robocomp/bin/robocompdsl") and os.access("/opt/robocomp/bin/robocompdsl",                                                                                 os.X_OK):
                robocompdsl_exe = "/opt/robocomp/bin/robocompdsl"
            elif os.path.isfile("~/robocomp/tools/robocompdsl/robocompdsl.py"):
                robocompdsl_exe = "python " + os.path.expanduser("~/robocomp/tools/robocompdsl/robocompdsl.py")
        if dry_run:
            print(robocompdsl_exe+' %file > /dev/null 2>&1' % cdsl_file)
            print(robocompdsl_exe+' %cdsl_file . > %log_file 2>&1' % (cdsl_file, log_file))
            return 0
        else:
            # completedProc = subprocess.Popen('robocompdsl %s > /dev/null 2>&1'%cdsl_file)
            # completedProc = subprocess.Popen('robocompdsl %s . > %s 2>&1' % (cdsl_file, log_file))

            command_output = subprocess.Popen(
                robocompdsl_exe + " %s" % cdsl_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, shell=True)
            stdout, stderr = command_output.communicate()
            with open("generation_output.log", "wb") as log:
                command_output = subprocess.Popen(
                    robocompdsl_exe+" %s ." % cdsl_file,
                    stdout=log,
                    stderr=log,
                    shell=True)
                stdout, stderr = command_output.communicate()
                # print(stdout)
                # print(stderr)
                return command_output.returncode
            return -1

    def cmake_component(self):
        """
        Execute cmake on the curren directory . Output and error is saved to make_output.log.
        :return: command return code
        """
        with open("cmake_output.log", "wb") as log:
            command_output = subprocess.Popen("cmake .",
                                              stdout=log,
                                              stderr=log,
                                              shell=True)
            stdout, stderr = command_output.communicate()
            # print(stdout)
            # print(stderr)
            return command_output.returncode

    def make_component(self, dry_run=True):
        """
        Execute the make for the component. Output and error is saved to make_output.log.
        :param dry_run: --dry-run is added as argument to the cmake command.
        :return: command return code
        """
        command = "make"
        if dry_run:
            command += " --dry-run"
        with open("make_output.log", "wb") as log:
            command_output = subprocess.Popen(command,
                                              stdout=log,
                                              stderr=log,
                                              shell=True)
            stdout, stderr = command_output.communicate()
            if dry_run:
                print(stdout)
            # print(stderr)
            return command_output.returncode

    def remove_genetared_files(self, current_dir, dry_run=True):
        """
        Remove all files but .smdsl, .cdsl and .log from the given dir.
        :param current_dir: Directory to look for files to remove.
        :param dry_run: Just show the output. No rm is really executed.
        :return: None
        """
        component_files = os.listdir(current_dir)
        # Remove not useful files
        for file in component_files:
            if not any(file.endswith(extension) for extension in (".smdsl", ".cdsl", ".log")):
                if dry_run:
                    print("rm -r %s" % file)
                else:
                    if os.path.isfile(file):
                        os.remove(file)
                    else:
                        rmtree(file)

    def check_components_generation(self, test_component_dir, dry_run, dirty, generate_only=False, filter="", ignore="",
                                    clean_only=False):
        """
        Main method of the class. Generate needed code, compile and show the results
        :param test_component_dir: alternative dir for the robocompdsl installation
        :param dry_run: just show what would be done. No file is removed.
        :param dirty: Leave all the generated files. No clean is done at the end of the script.
        :param generate_only: No compilation is executed for the components.
        :param filter: A string can be given to filter the directory of the components to be generated/compiled.
        :param clean_only: Just clean the generated files.
        :return: None
        """
        global_result = True
        self.dry_run = dry_run
        previous_dir = os.getcwd()
        os.chdir(os.path.expanduser(test_component_dir))
        list_dir = glob.glob("test_*")
        for item in list_dir:
            if os.path.isdir(item) and filter in item and not item.lower() == ignore.lower():
                current_dir = item
                cprint("Entering dir %s" % current_dir, 'magenta')
                os.chdir(current_dir)
                cdsl_file = None
                for file in glob.glob("*.cdsl"):
                    cdsl_file = file
                    break
                if cdsl_file:
                    # With the remove inside the cdsl_check we avoid cleaning dirs that don't have .cdsl files. Potentialy wrong directories.
                    self.remove_genetared_files(".", self.dry_run)
                    if clean_only:
                        cprint("\tCleaned", 'green')
                        os.chdir("..")
                        continue
                    self.valid += 1
                    self.results[current_dir] = {"generation":False, "compilation": False}
                    if self.generate_code(cdsl_file, "generation_output.log", False) == 0:
                        self.results[current_dir]['generation'] = True
                        self.generated += 1
                        if generate_only:
                            self.results[current_dir]['compilation'] = False
                            print("%s not compiled (-g option)" % current_dir)
                        else:
                            print("Executing cmake for %s ... WAIT!" % (current_dir))
                            self.cmake_component()
                            print("Executing make for %s ... WAIT!" % (current_dir))
                            make_result = self.make_component(self.dry_run)

                            if make_result == 0 or (make_result == 2 and self.dry_run):
                                self.results[current_dir]['compilation'] = True
                                self.compiled += 1
                                cprint("%s compilation OK" % current_dir, 'green')
                            else:
                                self.results[current_dir]['compilation'] = False
                                self.comp_failed += 1
                                cprint("%s compilation FAILED" % current_dir, 'red')
                                global_result = False
                    else:
                        cprint("%s generation FAILED"%os.path.join(current_dir,cdsl_file), 'red')
                        self.gen_failed += 1
                        self.results[current_dir]['generation'] = False
                        global_result = False
                    if not dirty:
                        self.remove_genetared_files(".", self.dry_run)
                print("")
                os.chdir("..")
        os.chdir(previous_dir)

        # Command final output
        if not clean_only:

            print("%d components found with cdsl" % self.valid)
            print("%d components generated OK (%d failed)" % (self.generated, self.gen_failed))
            print("%d components compiled OK (%d failed)" % (self.compiled, self.comp_failed))

            for current_dir, result in self.results.items():
                cname = colored(current_dir, 'magenta')

                # Printing results for generation
                if result['generation']:
                    gen_result = colored("TRUE", 'green')
                else:
                    gen_result = colored("FALSE", 'red')

                # Printing results for compilation
                if result['compilation']:
                    comp_result = colored("TRUE", 'green')
                else:
                    comp_result = colored("FALSE", 'red')

                if generate_only:
                    print("\t%s have been generated? %s" % (cname, gen_result))
                else:
                    print("\t%s have been generated? %s compile? %s" % (cname, gen_result, comp_result))
        return global_result


if __name__ == '__main__':
    parser = MyParser(description=colored(
        'This application generate components from cdsl files to check component generation/compilation\n', 'magenta'),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-g", "--generate-only", action="store_true",
                        help="Only the generation with robocompdsl is checked. No cmake or make is tested")
    parser.add_argument("-d", "--dirty",
                        help="No cleaning is done after execution. All source files and temp will be left on their dirs.",
                        action="store_true")
    parser.add_argument("-c", "--clean",
                        help="Just clean all source files and temp will be left on their dirs. .cdsl, .smdsl and .logs are kept on their dirs.",
                        action="store_true")
    parser.add_argument("-n", "--dry-run",
                        help="Executing dry run. No remove and make will be executed in dry run mode. CMake is executed and some files generated.",
                        action="store_true")
    parser.add_argument("-t", "--test-folder", type=str,
                        help=".",
                        default=TESTS_DIR)

    parser.add_argument("-f", "--filter", type=str,
                        help="Execute the check only for directories containing this string.", default="")
    parser.add_argument("-i", "--ignore", type=str,
                        help="Execute the check only for directories containing this string.", default="")
    args = parser.parse_args()

    try:
        checker = ComponentGenerationChecker()
        checker.check_components_generation(args.test_folder, args.dry_run, args.dirty, args.generate_only,
                                            args.filter, args.ignore,
                                            args.clean)
    except (KeyboardInterrupt, SystemExit):
        cprint("\nExiting in the middle of the execution.", 'red')
        cprint("Some files will be left on the directories.", 'yellow')
        cprint("Use -c option to clean all the generated files.", 'yellow')
        sys.exit()
    except Exception as e:
        cprint("Unexpected exception: %s"%e, 'red')
        traceback.print_stack()

