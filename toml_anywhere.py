"""
Toml Everywhere

A wrapper that allows any command line program to have a `--config` flag.
No explicit support required!

Call as:

$ toml_everywhere.py program [argument ...] --config config.cfg

Toml Everywhere will translate the config file values to command line
arguments for the command. The command will then be invoked to run
the specified options. This works for any set of arguments in the TOML,
and can be used to wrap any command line program.

Pass "-" as the command to only print the arguments to stdout.
"""

import sys
import json
import shlex
import argparse
import datetime
import subprocess
from pprint import pprint

# Use tomllib if avaliable
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def generate_pairs(config):
    for key, value in config.items():
        key = key.replace('_', '-')

        if isinstance(value, dict):
            # key is actually a table, not a key value pair
            # recursively parse args
            for part_key, part_value in generate_pairs(value):
                yield f"{key}.{part_key}", part_value
        else:
            # Restore TOML date format
            # datetime.isoformat() spec is ISO 8601 compliant and RFC 3339 compliant
            if isinstance(value, (datetime.datetime, datetime.date)):
                value = value.isoformat()

            # Format value as JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value)

            yield key, value


def config_to_args(config):
    """
    Parse config and make a list of arguments from config file.
    """
    args = []

    for key, value in generate_pairs(config):
        args.extend([f"--{key}", f"{value}"])

    return args


def args_to_cmd(args):
    """
    Quote arguments for placing in a shell command.

    Meant for printing command, not strictly for shell escaping.

    For example a literal new line on the command line is printed as "\n",
    even though a shell likely would not expand this back to a literal newline.
    """
    # Using repr to escape whitespace
    return " ".join([shlex.quote(repr(x)[1:-1]) for x in args])


def split_args(args):
    """
    Split arguments into process internal arguments,
    the command to execute, and the arguments for the command.

    The command is will be kept as the last internal argument.
    """
    # Find index of last internal arguement
    i = 0
    while i < len(args):
        if args[i] == "--flag":
            # Skip flag value
            i += 2
        elif args[i] == "--":
            # Marker to stop argument parsing
            # Assume command is next
            i += 1
            break
        elif args[i] == "-":
            # Dryrun command
            break
        elif args[i].startswith("-"):
            # Assume to be a flag argument, argparse will validate
            i += 1
        else:
            # Non-flag encountered, assume to be command
            # argparse will validate
            break

    # Split args
    internal_args, command, external_args = args[:i], args[i], args[i + 1:]

    # Remove "--"
    if command == "--":
        # Make command
        command, external_args = external_args[:1], external_args[1:]

    return internal_args + [command], external_args


def main(args = None):
    parser = argparse.ArgumentParser(
        description = "Load command line arguments from TOML configuration for any program.",
        add_help = False)

    parser.add_argument("-h", "--help", action = "help",
        help = "Show this help message and exit.")
    parser.add_argument("--version", action = "version",
        help = "Show program's version number and exit.")

    print_group = parser.add_mutually_exclusive_group()
    # Can only specify one print out type at a time
    print_group.add_argument("-p", "--print", action = "store_true",
        help = "Print command line arguments before command is called. "
               "Specify only one of --print, --pretty-print, --list.")
    print_group.add_argument("--pprint", "--pretty-print", action = "store_true",
        dest = "pretty_print",
        help = "Pretty print command line arguments immediatly before command is called. "
               "Specify only one of --print, --pretty-print, --list.")
    print_group.add_argument("-l", "--list", action = "store_true",
        help = "Print command line arguments as a list before command is called. "
               "Specify only one of --print, --pretty-print, --list.")

    parser.add_argument("-d", "--dryrun", action = "store_true",
        help = "Show command, but do not run it. Affected by print mode flags. "
               "Implied by setting command to '-'.")
    parser.add_argument("--flag", default = "--config",
        help = "Command line flag replace for command arguments. Default is '--config'.")
    parser.add_argument('command',
        help = "Path to executable to call. '-' causes the commands to just be printed.")

    if not args:
        args = sys.argv[1:]

    if not args:
        # Just show help
        parser.print_help()
        parser.exit()

    internal_args, external_args = split_args(args)

    # Parse internal arguments (and exit on failure)
    internal_args = parser.parse_args(internal_args)

    # Command of "-" or dryrun implies print
    if internal_args.command == "-":
        internal_args.dryrun = True

    if (internal_args.dryrun
        and not internal_args.list and
        not internal_args.print
        and not internal_args.pretty_print):
        # Default to printing
        internal_args.print = True

    # Build new command args list from given args
    command_args = []

    # Combine config results into argument list
    i = 0
    while i < len(external_args):
        if external_args[i] == internal_args.flag:
            if i + 1 >= len(external_args):
                # No given value
                parser.error("--config: Expected one argument")

            # Next argument is config file
            config = external_args[i + 1]

            if config.startswith("-"):
                # Is a flag, not a config file
                parser.error("--config: Expected one argument")

            try:
                with open(config, "rb") as f:
                    config_data = tomllib.load(f, parse_float = str)
            except IOError as exc:
                parser.exit(2, f"Failed to parse config: {exc}\n")
            except tomllib.TOMLDecodeError as exc:
                parser.exit(2, f"Failed to parse config: {exc}: {config!r}\n")

            command_args.extend(config_to_args(config_data))
            i += 1

        elif external_args[i].startswith(internal_args.flag + "="):
            # Config file is embedded in argument
            config = external_args[i][len(internal_args.flag + "="):]

            try:
                with open(config, "rb") as f:
                    config_data = tomllib.load(f, parse_float = str)
            except IOError as exc:
                parser.exit(2, f"Failed to parse config: {exc}\n")
            except tomllib.TOMLDecodeError as exc:
                parser.exit(2, f"Failed to parse config: {exc}: {config!r}\n")

            command_args.extend(config_to_args(config))

        else:
            # Argument is not config
            command_args.append(external_args[i])

        i += 1

    # Use command and arguments as requested
    if internal_args.command != "-":
        # Prepend command
        command_args.insert(0, internal_args.command)

    if internal_args.list:
        # Just print list
        print(command_args)
    elif internal_args.print:
        # Format args for printing
        print(args_to_cmd(command_args))
    elif internal_args.pretty_print:
        # Pretty Print
        pprint(command_args)
    elif internal_args.print:
        print('\n'.join(command_args))

    # Run it
    if not internal_args.dryrun:
        try:
            subprocess.run(command_args)
        except IOError as exc:
            # Suppress stack trace, as caused by external program execution
            parser.exit(1, f"{type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
