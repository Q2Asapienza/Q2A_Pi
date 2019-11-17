# DEPRECATED - Q2A_Pi


Interface for python for communicating with q2a.di.uniroma1.it

## Deprecated, why?

Python is cool and everything but it's more likely to find a cheap webserver capable of running PHP, than one capable of running python, so the library was good only for testing purposes.

From now on updates will only be done to the new [PHP version](https://github.com/Q2Asapienza/Q2A-php-interface) of the library.

## Setup

To use the library simply clone it into your project directory
```
git clone https://github.com/fc-dev/Q2A_Pi
```
Or add it as a submodule if you are working in a git repository
```
git submodule add https://github.com/fc-dev/Q2A_Pi
```

Then you can use it from python by simply importing it this way:
```python
import Q2A_Pi
```
or if you prefer to use the classes directly without having to write the package name:
```python
from Q2A_Pi import *
```
Check out the [wiki]() for basic usages example

### Prerequisites

To run the program you need python (3.7.4) installed, and the libraries:
```
requests
lxml
cssselect
```
With their dependencies too.

## Contributing

If you want to help with this project contact me or do a pull request.



## Authors

* **Federico Capece** - whole repository (for now) - [fc-dev](https://github.com/fc-dev)

See also the list of [contributors](https://github.com/fc-dev/Sankaku-Downloader/contributors) who participated in this project.

## License

This project is licensed under the GPL3 License - see the [LICENSE](LICENSE) file for details
