import json


def load_access_token():
    with open('tokeninfo.json', 'r') as f:
        data = json.load(f)
        return data['access_token']


def main():
    print(f'Access token: {load_access_token()}')


if __name__ == '__main__':
    main()