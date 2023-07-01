import hashlib
import click

algos = ["sha1", "sha256", "sha512", "md5"]


def input_file_option(prompt):
    return click.option(
        "--input-file", "-if",
        required=True,
        type=click.File(mode="rb"),
        help="Path to file for hashing",
        prompt=prompt,
    )


def algorithm_option():
    return click.option(
        "--algorithm", "-a",
        required=True,
        type=click.Choice(algos, case_sensitive=False),
        help="The type of hashing algorithm used",
        prompt="Hash algorithm to use",
    )


def hash_option():
    return click.option(
        "--hash-value", "-h",
        required=True,
        type=click.STRING,
        help="Hash value to check against",
        prompt="Hash value to check",
    )


@click.group()
def cli():
    pass


@click.command()
@input_file_option("File to be hashed")
@algorithm_option()
def get_hash(input_file, algorithm):
    """
    Get the hash of a single file"""
    hasher = getattr(hashlib, algorithm)()
    for chunk in iter(lambda: input_file.read(4096), b""):
        hasher.update(chunk)
    click.echo(hasher.hexdigest())


@click.command()
@input_file_option("File to be checked")
@algorithm_option()
@hash_option()
def check_hash(input_file, algorithm, hash_value):
    """Check the has of an existing file"""
    hasher = getattr(hashlib, algorithm)()
    for chunk in iter(lambda: input_file.read(4096), b""):
        hasher.update(chunk)
    if hasher.hexdigest() == hash_value:
        click.echo("Hash matched!")
    else:
        click.echo("Hash did not match.")


cli.add_command(get_hash)
cli.add_command(check_hash)

if __name__ == '__main__':
    cli()
