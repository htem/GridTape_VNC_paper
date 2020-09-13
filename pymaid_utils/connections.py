#!/usr/bin/env python
#Requires python 3.6+ for f-strings

import os
import json

import pymaid


def connect_to_catmaid(config_filename='catmaid_configs.json'):
    if not os.path.exists(config_filename):
        config_filename = os.path.join(os.path.dirname(__file__),
        'connection_configs', config_filename)
    try:
        with open(config_filename, 'r') as f:
            configs = json.load(f)
    except:
        print(f'ERROR: No {config_filename} file found, or file improperly'
              ' formatted. See catmaid_configs_virtualflybrain.json for an'
              ' example config file that works.')
        raise

    catmaid_http_username = configs.get('catmaid_http_username', None)
    catmaid_http_password = configs.get('catmaid_http_password', None)


    # --Source project-- #
    if all([configs.get('source_catmaid_url', None),
            configs.get('source_catmaid_account_to_use', None),
            configs.get('source_project_id', None)]):
        source_project = pymaid.CatmaidInstance(
            configs['source_catmaid_url'],
            configs['catmaid_account_api_keys'][
                configs['source_catmaid_account_to_use']
            ],
            http_user=catmaid_http_username,
            http_password=catmaid_http_password,
            make_global=False
        )
        source_project.project_id = configs['source_project_id']
        print_project_name(source_project, 'Source project:')
    else:
        raise ValueError('The following fields must appear in'
                         f' {config_filename} and not be null:'
                         " 'source_catmaid_url',"
                         " 'source_catmaid_account_to_use',"
                         " and 'source_project_id'")


    # --Target project-- #
    # target_project is only used by upload_or_update_neurons, and may be
    # ommitted from the config file when you only want to do read-only
    # operations.
    if all([configs.get('target_catmaid_url', None),
            configs.get('target_catmaid_account_to_use', None),
            configs.get('target_project_id', None)]):
        target_project = pymaid.CatmaidInstance(
            configs['target_catmaid_url'],
            configs['catmaid_account_api_keys'][
                configs['target_catmaid_account_to_use']
            ],
            http_user=catmaid_http_username,
            http_password=catmaid_http_password,
            make_global=False
        )
        target_project.project_id = configs['target_project_id']
        print_project_name(target_project, 'Target project:')

    elif any([configs.get('target_catmaid_url', None),
              configs.get('target_catmaid_account_to_use', None),
              configs.get('target_project_id', None)]):
        print('WARNING: You have configured some target project variables but'
              ' not all. The following fields must appear in'
              f" {config_filename} and not be null: 'target_catmaid_url',"
              " 'target_catmaid_account_to_use', and 'target_project_id'."
              ' Continuing without a target project.')

    try:
        return source_project, target_project
    except:
        return source_project


def print_project_name(project, title=None):
    print(
        title,
        project.project_id,
        project.available_projects[
            project.available_projects.id == project.project_id
        ].title.to_string().split('    ')[1]
    )


def get_source_project_id():
    print_project_name(source_project, 'Source project:')
    return source_project.project_id


def set_source_project_id(project_id):
    source_project.project_id = project_id
    return get_source_project_id()


def get_target_project_id():
    print_project_name(target_project, 'Target project:')
    return target_project.project_id


def set_target_project_id(project_id):
    target_project.project_id = project_id
    return get_target_project_id()


def set_project_ids(source_id, target_id=None):
    if target_id is None:
        target_id = source_id
    set_source_project_id(source_id)
    set_target_project_id(target_id)


def get_project_ids():
    return get_source_project_id(), get_target_project_id()


def clear_cache():
    # I had a few instances where this didn't seem to work. (Namely, I pulled data,
    # modified a neuron on catmaid, cleared cache, then re-pulled data,
    # but the old neuron seemed to still be present in memory.)
    # Maybe this doesn't work reliably, so try not to trust it.
    # Calling reconnect_to_catmaid is a more reliable way to clear cached data.
    source_project.clear_cache()
    try:
        target_project.clear_cache()
    except NameError:
        pass

