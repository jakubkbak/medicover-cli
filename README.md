# Installation

1. Create a virtualenv

  ```bash
  mkvirtualenv medicover-cli

  ```

2. Install the package

  ```bash
  pip install git+git@github.com:jakubkbak/medicover-cli.git
  ```
  or clone and then install 
  ```bash
  git clone git@github.com:jakubkbak/medicover-cli
  pip install .
  ```

# Usage

### Providing credentials

There are two ways:

1. Set the credentials as env variables:

  ```bash
  export MEDICOVER_USER=your_card_number
  export MEDICOVER_PASSWORD=your_password
  ```

2. Provide the credentials as arguments to the main command:

  ```bash
  medicover -u your_card_number -p your_password form
  ```

### Running

After installing with pip, you can simply run 'medicover' in bash to run the app.

### Subcommands

Right now the only command is 'form' which starts the interactive visit booking form.
Hopefully, there will be more ;)

Example (credentials from evn):

```bash
medicover form
```