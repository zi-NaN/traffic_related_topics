'''
Author:          ZHAO Zinan
Written:         2018-07-04
Last Updated:    2018-09-18

track people (match persons with the detected rectangles)
'''

import copy
from person import Person

class PeopleTracker:
    _people = []
    _name_index = 1
    _frame = 1
    _people_options = {}

    def __init__(self, people_options=None):
        if people_options is not None:
            self._people_options = people_options

    def people(self, rects):
        current_people = []
        matches = {}
        self._frame += 1

        # check my current people for matches
        for person in self._people:
            person.tick()  # age everyone
            
            for rect in rects:
                match = person.match(rect)
                key = self._rect_key(rect)
                if match > 0:
                    # not in matches or have a better match
                    if key not in matches or match > matches[key][1]:
                        cleaned_matches = {}
                        add = True
                        for _key in matches:
                            if matches[_key][0] == person:
                                # we already have a better match
                                if matches[_key][1] > match:
                                    cleaned_matches[_key] = matches[_key]
                                    add = False
                            else:
                                cleaned_matches[_key] = matches[_key]

                        if add:
                            cleaned_matches[key] = (person, match, rect)

                        matches = cleaned_matches
                else:
                    pass
                    # print('%s is not a match for %s' % (person.name, key))

        # touch best matches
        for key in matches:
            match = matches[key]
            person = match[0]
            person.set_rect(match[2])
            current_people.append(person)

        for person in self._people:
            if person.is_dead():
                pass

        # find new people
        for rect in rects:
            key = self._rect_key(rect)
            if key not in matches:
                options = copy.deepcopy(self._people_options)
                options['name'] = 'Person %d' % self._name_index
                options['rect'] = rect
                person = Person(**options)
                current_people.append(person)
                self._name_index += 1

        # filter out anyone who is dead
        for person in self._people:
            if not person.is_dead() and person not in current_people:
                current_people.append(person)

        self._people = current_people

        return current_people

    def _rect_key(self, rect):
        return '%d-%d-%d-%d' % (rect[0], rect[1], rect[2], rect[3])

    def least_remaining_time(self, width):
        least_t = float('inf')

        # cal the remain time for each person
        for person in self._people:
            # from right to left
            if person.pspeed < 0:      
                person.remain_t = person._center[0]/abs(person.pspeed) if person.direction=='r' else float('inf')

            # from left to right
            elif person.pspeed > 0:    
                person.remain_t = (width - person._center[0])/abs(person.pspeed) if person.direction=='l' else float('inf')


            least_t = min(person.remain_t, least_t)

        return least_t if least_t else float('inf') # if least_t is None, return inf

