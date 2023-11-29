NAME: str = "gfagraphs"
AUTHOR: str = "Siegfried Dubois",
AUTHOR_EMAIL: str = "siegfried.dubois@inria.fr",
LICENCE: str = "LICENCE"
DESCRIPTION: str = "Library to parse, edit and handle in memory GFA graphs"
REQUIRED_PYTHON: tuple = (3, 10)
WORKSPACE: str = ""
MAIN_MODULE: str = ""
MAIN_FUNC: str = ""

# Change this to ovveride default version number
OVERRIDE_VN: bool = True
VN: str = "0.2.0"

# Fill this part if your tool features command-line interface
HAS_COMMAND_LINE: bool = False
COMMAND: dict = {'console_scripts': [
    f'{NAME}={WORKSPACE}.{MAIN_MODULE}:{MAIN_FUNC}']}
