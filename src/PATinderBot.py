'''
PATinderBot: automatically like and capture Tinder recommendations
Copyright (C) 2016  physicalattraction

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import json
import requests
import sys
from shutil import copyfile
from pprint import pprint  # @UnusedImport
from os.path import os

from PACollageCreator import PACollageCreator
from PATinderUser import PATinderUser


class PATinderBot:

    def __init__(self):
        self.__read_secrets_file()
        self.__read_schools_file()
        self.headers = {
            'app_version': '3',
            'platform': 'ios'
        }

    def run_tinder_bot(self):
        print('Tinder bot is running')

        for user in self._recommendations():

            if user is None:
                break

            action = self._like_or_nope(user)
            if action == 'like':
                match = self._like(user)
                if match:
                    status = 'match'
                else:
                    status = 'like'
            elif action == 'nope':
                status = 'nope'
                self._nope(user)

            if action != 'no_action':
                self._create_photo_cards(user, status)

        print('Tinder bot is finished')

    def _recommendations(self):
        h = self.headers
        h.update({'X-Auth-Token': self.__get_tinder_auth_token()})
        r = requests.get('https://api.gotinder.com/user/recs', headers=h)
        if r.status_code == 401:
            raise Exception('HTTP Error 401 Unauthorized')
        elif r.status_code == 504:
            raise Exception('HTTP Error 504 Gateway timeout')

        if 'results' not in r.json():
            print(r.json())

        for result in r.json().get('results'):
            yield PATinderUser(result)

    def _like(self, user):
        print(' -> Like {} ({})'.format(user.name, user.id))
        try:
            u = 'https://api.gotinder.com/like/{}'.format(user.id)
            d = requests.get(u, headers=self.headers, timeout=0.7).json()
            return d.get('match')
        except KeyError:
            # Only raise key errors
            raise
        except:
            # Ignore all other errors
            pass

    def _nope(self, user):
        print(' -> Nope {} ({})'.format(user.name, user.id))
        try:
            u = 'https://api.gotinder.com/pass/{}'.format(user.id)
            requests.get(u, headers=self.headers, timeout=0.7).json()
        except KeyError:
            # Only raise key errors
            raise
        except:
            # Ignore all other errors
            pass

    def _like_or_nope(self, user):
        '''Determine the 'like action' for the given user: like, nope or no_action

        If there is at least one good school: like
        If not, if there is at least one unknown school: no_action
        If not: nope
        '''
        unknown_school = False
        for school in user.schools:
            school_id = school.get('id')
            if school_id in self.schools:
                if self.schools[school_id] == 1:
                    return 'like'
            else:
                self.__update_schools(school)
                unknown_school = True
        if unknown_school:
            return 'no_action'
        else:
            return 'nope'

    def _create_photo_cards(self, user, status):
        collageCreator = PACollageCreator()
        for photo in user.d['photos']:
            collageCreator.download_img(url=photo['url'])

        collageCreator.create_collage(user, status)

    def __read_secrets_file(self):
        secrets_file = self.__get_secrets_file_name()
        with open(secrets_file) as f:
            self.secrets = json.loads(f.read())

    def __read_schools_file(self):
        self.schools = dict()
        schools_file = self.__get_schools_file_name()
        if not os.path.isfile(schools_file):
            schools_template_file = 'schools_template.json'
            copyfile(schools_template_file, schools_file)
        with open(schools_file) as f:
            for school in json.loads(f.read()):
                school_id = school.get('id')
                if school_id in self.schools:
                    print('School with id {} occurs multiple times in {}'.
                          format(school_id, schools_file))
                self.schools[school_id] = school.get('status')

    def __get_json_dir(self):
        current_dir = os.path.dirname(__file__)
        json_dir = os.path.join(current_dir, '..', 'json')
        return json_dir

    def __get_secrets_file_name(self):
        secrets_file = 'secrets.json'
        return os.path.join(self.__get_json_dir(), secrets_file)

    def __get_schools_file_name(self):
        schools_file = 'schools.json'
        return os.path.join(self.__get_json_dir(), schools_file)

    def __get_tinder_auth_token(self):
        h = self.headers
        h.update({'content-type': 'application/json'})
        req = requests.post(
            'https://api.gotinder.com/auth',
            headers=h,
            data=json.dumps({'facebook_id': self.secrets.get('FACEBOOK_ID'),
                             'facebook_token': self.secrets.get('FACEBOOK_AUTH_TOKEN')
                             })
        )
        try:
            token = req.json().get('token')
        except:
            token = None

        if token is None:
            print('ERROR: Could not get token')
            sys.exit(0)

        return token

    def __update_schools(self, school):
        schools_file = self.__get_schools_file_name()
        print(' -> Adding school {} to {}'.format(school.get('name'), schools_file))
        with open(schools_file) as f:
            schools = json.loads(f.read())
        schools.append({'id': school.get('id'),
                        'name': school.get('name'),
                        'status': 2})
        with open(schools_file, 'w') as outfile:
            json.dump(schools, outfile, indent=4)

if __name__ == '__main__':
    tinder_bot = PATinderBot()
    tinder_bot.run_tinder_bot()