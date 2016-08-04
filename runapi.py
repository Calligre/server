#!/usr/bin/env python
import api


def main():
    api.app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
