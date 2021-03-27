"""
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
"""

import random
import time

from ProfileJudge.profile_judge import ProfileJudge
from collage_creator import CollageCreator
from enums import Status, SwipeAction
from secrets import TINDER_USER_ID, get_from_secrets
from tinder_service import TinderService
from tinder_user import TinderUser


class TinderBot:
    MAX_NUMBER_OF_PHOTOS = 6

    _collage_creator: CollageCreator = None

    def __init__(self):
        self.profile_judge = ProfileJudge()
        self.service = TinderService()
        self.user = self.service.get_user(get_from_secrets(TINDER_USER_ID))
        print(f'TinderBot initialized for {self.user.name}')

    def run(self):
        print('Tinder bot is running')

        for user in self.service.get_recommendations():
            if user is None:
                break

            action = self.profile_judge.like_or_nope(user)
            if action == SwipeAction.like:
                match = self.service.like(user)
                if match:
                    status = Status.matched
                else:
                    status = Status.liked
                self._create_photo_cards(user, status)
                # self._add_user_to_user_list(user, status)
            elif action == SwipeAction.nope:
                self.service.nope(user)
                # In order to not look like a bot, we wait a random time around 1 second
                # For like this is not necessary, since we create photo collage for them,
                # which takes a similar amount of time
                time.sleep(random.uniform(0.7, 1.2))
                # TODO: Refactor to have three user list objects, and append it to the correct one
                # self._add_user_to_user_list(user, status=Status.noped)
            elif action == SwipeAction.no_action:
                # Explicitly do nothing
                pass

            break

        print('Tinder bot is finished\n')

    def analyze_photo_success_rate(self):
        """
        Analyze the photo success rates of the user
        """

        print('*** Photo analysis ***\n')
        for photo in self.user.photos:
            url = photo.get('url')
            select_rate = photo.get('selectRate')
            success_rate = photo.get('successRate')
            print(f'{url}: select rate = {select_rate}, success rate = {success_rate}')
        print('\n')

    def _create_photo_cards(self, user: TinderUser, status: Status):
        collage_creator = CollageCreator()
        for photo_index, photo in enumerate(user.d['photos']):
            if photo_index < self.MAX_NUMBER_OF_PHOTOS:
                collage_creator.download_img(url=photo['url'])
        collage_creator.create_collage(user, status)


if __name__ == '__main__':
    tinder_bot = TinderBot()
    tinder_bot.run()
