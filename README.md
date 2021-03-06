## Pinylib

RTMP module for tinychat chat rooms.


pinylib (originally called [tinylib](https://github.com/nortxort/tinylib)) provides classes/methods/functions to create a connection to a tinychat chat room. The idea of the module was to create a base in which developers could build their own entertainment/helper bots with.

The file [pinylib.py](https://github.com/nortxort/pinylib/blob/master/pinylib.py) is somewhat built over a file made by [MegaLoler](http://pastebin.com/u/MegaLoler "MegaLoler files on pastebin") and can be found [here](http://pastebin.com/0CYCisB5). Since this file is from 2012, a lot of modifications has been made to reflect the changes tinychat has made over the years. 

## Setting up

Examples shown here, assumes you are using windows.

pinylib was developed using [python 2.7.10](https://www.python.org/downloads/windows/ "python for windows") so this is the recomended python interpreter. Later versions of python should work to, aslong as they are from the 2.7 family. 

### Requirements

pinylib requires 5 libraries that are not part of the standard python library, these being:

* [pyamf](https://github.com/hydralabs/pyamf "pyamf")
* [requests](https://github.com/kennethreitz/requests "requests")
* [colorama](https://github.com/tartley/colorama "Colorama")
* [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/ "beautifulsoup4")
* [selenium](http://selenium-python.readthedocs.io/)

These can all be installed form a command prompt with pip.

`pip install pyamf requests colorama beautifulsoup4 selenium`

In the case of selenium, read the [installation documentation](http://selenium-python.readthedocs.io/installation.html) as it requires a [driver](http://selenium-python.readthedocs.io/installation.html#drivers).


For more info, see the [wiki](https://github.com/nortxort/pinylib/wiki/Requirements)


## Run the client

Run the client by typing `python path\to\sample_client.py` in a command prompt.

## Submitting an issue.
Issues posted should be about pinylib and **only** pinylib. 

Before submitting an issue, please read through the [issues](https://github.com/nortxort/pinylib/issues) section, including already closed issues. If you do not find an answer to your issue, then please provide as much info as possible when opening an issue. Possible info could be:

* Python version including subversion.
* Pinylib version.
* Debug log.
* How to reproduce the issue/error.


## Author

* [nortxort](https://github.com/nortxort)

## License

The MIT License (MIT)

Copyright (c) 2016 nortxort

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute,
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice
shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Acknowledgments
*Thanks to the following people who in some way or another, has helped with this project*

* [MegaLoler](http://pastebin.com/u/MegaLoler)

* [prekageo](https://github.com/prekageo/rtmp-python)

* [Anorov](https://github.com/Anorov/PySocks)

* [notnola](https://github.com/notnola)

* [GoelBiju](https://github.com/GoelBiju)

* [Autotonic](https://github.com/Autotonic)

