#!/usr/bin/env python
import api


def main():
    api.app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    main()
