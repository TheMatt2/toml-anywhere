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

The following rules are followed:

| TOML Type | Note                                                                                                         | Example TOML                        | Example Command                          |
| --------- | ------------------------------------------------------------------------------------------------------------ | ----------------------------------- | ---------------------------------------- |
| Bool      | `true` specifies the key should be passed as a command line flag. `false` specifies the key will be omitted. | `verbose = true`                    | `--verbose`                              |
| Float     | Floats are preserved as strings, and passed as command line arguments.                                       | `exponent = 1E10_000`               | `--exponent 1E10_000`                    |
| Date      | Dates and date times are converted to ISO 8601 format (`datetime.isoformat()`).                              | `start_date = 1979-05-27T07:32:00Z` | `--start-date 1979-05-27T07:32:00+00:00` |
