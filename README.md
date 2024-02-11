# TOML Anywhere!

A wrapper that allows any command line program to have a --config flag. No explicit support required!

## Usage

```
$ toml_everywhere.py program [argument ...] --config config.cfg
```

Toml Everywhere will translate the config file values to command line
arguments for the command. The command will then be invoked to run
the specified options. This works for any set of arguments in the TOML,
and can be used to wrap any command line program.

Pass "-" as the command to only print the arguments to stdout.

Key, value pairs in the TOML configuration file and translated into
command line arguments.

