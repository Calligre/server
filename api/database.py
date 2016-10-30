import os
import traceback

import flask_api
import psycopg2


DB_BASE = os.environ.get('DB_BASE', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', 'postgres')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', 5432)

db = psycopg2.connect(database=DB_BASE, user=DB_USER, password=DB_PASS,
                      host=DB_HOST, port=DB_PORT)


def delete(_resource, query, params):
    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
            db.commit()

            affected = cursor.rowcount
    except Exception:
        traceback.print_exc()
        data = {'errors': [{
            'title': 'database error',
            'detail': 'could not delete record'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    if not affected:
        data = {'errors': [{'title': 'no record found'}]}
        return data, flask_api.status.HTTP_404_NOT_FOUND

    data = {'data': None}
    return data, flask_api.status.HTTP_204_NO_CONTENT


def get(resource, query, params):
    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
            columns = [d[0] for d in cursor.description]
            record = cursor.fetchone()
    except Exception:
        traceback.print_exc()
        data = {'errors': [{
            'title': 'database error',
            'detail': 'could not get record'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    if not record:
        data = {'errors': [{'title': 'no record found'}]}
        return data, flask_api.status.HTTP_404_NOT_FOUND

    item = dict(zip(columns, record))
    data = {'data': {'type': resource, 'id': item['id'], 'attributes': item}}
    return data, flask_api.status.HTTP_200_OK


def gets(resource, query, params=None):
    params = params or dict()

    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
            columns = [d['name'] for d in cursor.description]
            records = cursor.fetchall()
    except Exception:
        traceback.print_exc()
        data = {'errors': [{
            'title': 'database error',
            'detail': 'could not get records'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    data = {'data': list()}
    for record in records:
        item = dict(zip(columns, record))
        item = {'type': resource, 'id': item['id'], 'attributes': item}
        data['data'].append(item)

    return data, flask_api.status.HTTP_200_OK


def patch(_resource, query, params):
    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
            db.commit()

            affected = cursor.rowcount
    except Exception:
        traceback.print_exc()
        data = {'errors': [{
            'title': 'database error',
            'detail': 'could not patch record'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    if not affected:
        data = {'errors': [{'title': 'no record found'}]}
        return data, flask_api.status.HTTP_404_NOT_FOUND

    data = {'data': None}
    return data, flask_api.status.HTTP_204_NO_CONTENT


def post(resource, query, params):
    try:
        with db.cursor() as cursor:
            cursor.execute(query, params)
            uuid = cursor.fetchone()[0]
            db.commit()
    except Exception:
        traceback.print_exc()
        data = {'errors': [{
            'title': 'database error',
            'detail': 'could not post record'}]}
        return data, flask_api.status.HTTP_500_INTERNAL_SERVER_ERROR

    data = {'data': {'type': resource, 'id': uuid}}
    return data, flask_api.status.HTTP_201_CREATED
