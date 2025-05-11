import random
import re
from enum import Enum
from typing import Any

import chevron
import lxml.html
import prairielearn as pl
from typing_extensions import assert_never

CORRECT_ANSWER_DEFAULT = None
SHOW_PERCENTAGE_SCORE_DEFAULT = True
SHOW_PARTIAL_SCORE_DEFAULT = True
EMPTY_CACHE_DEFAULT = False
GRADE_MODE_DEFAULT = 'through-first'
WEIGHT_DEFAULT = '1'

CACHE_ACCESS_TABLE_MUSTACHE_TEMPLATE_NAME = 'pl-cache-access-table.mustache'


def prepare(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    required_attribs = ['answers-name']
    optional_attribs = [
        'show-partial-score',
        'show-percentage-score',
        'empty-cache',
        'grade-mode',
        'weight',
    ]
    pl.check_attribs(element, required_attribs, optional_attribs)

    name = pl.get_string_attrib(element, 'answers-name')
    pl.check_answers_names(data, name)

    try:
        accesses = data['correct_answers'][name]
    except AttributeError:
        print(f"Sequence of cache accesses not found in data['correct_answers'][{name}]")

    for i in range(len(accesses)):
        if not isinstance(accesses[i]['address'], str):
            raise AttributeError('Addresses need to be a string in data["correct_answers"]')
        if not isinstance(accesses[i]['hit'], bool):
            raise AttributeError('Hit need to be a Boolean in data["correct_answers"]')
    

    return

def render(element_html: str, data: pl.QuestionData) -> str:

    element = lxml.html.fragment_fromstring(element_html)
    name = pl.get_string_attrib(element, 'answers-name')
    # Get the output name

    show_partial_score = pl.get_boolean_attrib(
        element, 'show-partial-score', SHOW_PARTIAL_SCORE_DEFAULT
    )  # Default to False if not specified

    show_percentage_score = pl.get_boolean_attrib(
        element, 'show-percentage-score', SHOW_PERCENTAGE_SCORE_DEFAULT
    )  # Default to False if not specified

    empty_cache = pl.get_boolean_attrib(
        element, 'empty-cache', EMPTY_CACHE_DEFAULT
    )  # Default to False if not specified

    grade_mode = pl.get_string_attrib(element, 'grade-mode', GRADE_MODE_DEFAULT)

    if grade_mode != 'through-first' and grade_mode != 'all' and grade_mode != 'all-or-nothing':
        raise AttributeError('grade-mode must be "through-first" or "all" or "all-or-nothing')

    accesses = data['correct_answers'][name]

    access_data = []
    for i in range(len(accesses)):
        raw_sub = data['raw_submitted_answers'].get(f'{name}{i}_hit', None)
        sub_hit = False
        sub_miss = False
        sub_text = None
        if raw_sub != None:
            if raw_sub == 'Hit':
                sub_hit = True
                sub_text = 'Hit'
            else:
                sub_miss = True
                sub_text = 'Miss'
        ans_text = None
        if accesses[i]['hit'] == True:
            ans_text = 'Hit'
        else:
            ans_text = 'Miss'

        first_miss = False
        if i == 0 and empty_cache == True:
            first_miss = True

        access = {
            'address': accesses[i]['address'],
            'hit': accesses[i]['hit'],
            'index': i,
            'sub_hit': sub_hit,
            'sub_miss': sub_miss,
            'sub_text': sub_text,
            'ans_text': ans_text,
            'correct': False,
            'incorrect': False,
            'first_miss': first_miss,
            'input_error': data['format_errors'].get(f'{name}{i}_hit', None),
        }
        hit_score = data['partial_scores'].get(f'{name}{i}_hit')
        if hit_score != None and show_partial_score:
            if hit_score['score'] == 1:
                access['correct'] = True
            else:
                access['incorrect'] = True

        access_data.append(access)

    #print(cache_sets)
    correct = False
    partial = False
    incorrect = False

    partial_score = data['partial_scores'].get(name)
    if partial_score != None:
        score = round(partial_score['score'] * 100, 2)
        if score == 100:
            correct = True
        elif score > 0:
            partial = True
        else:
            incorrect = True
    else:
        score = None

    grade_info = ''
    if grade_mode == 'through-first':
        grade_info = 'This table will be graded only until first error'
    elif grade_mode == 'all':
        grade_info = 'Each hit/miss choice will be graded independently'
    else:
        grade_info = 'Each hit/miss choice will be graded independently. If any response is incorrect, no credit will be awarded'

    if not show_partial_score:
        grade_info += '<br>Partial score information will not be shown'

    if not show_percentage_score:
        grade_info += '<br>Total percentage score for this table will not be shown'

    # Get template
    with open(CACHE_ACCESS_TABLE_MUSTACHE_TEMPLATE_NAME, 'r', encoding='utf-8') as f:
        template = f.read()
    if data['panel'] == 'question':
        grading_text = 'PLACEHOLDER'
        info_params = {
            'format': True,
            'grading_text': grading_text,
        }
        info = chevron.render(template, info_params)
        html_params = {
            'question': True,
            'name': name,
            'info': info,
            'uuid': pl.get_uuid(),
            'accesses': access_data,
            'score': score,
            'all_correct': correct,
            'all_incorrect': incorrect,
            'all_partial': partial,
            'show-partial-score': show_partial_score,
            'show-percentage-score': show_percentage_score,
            'feedback': data['feedback'].get(name, None),
            'grade-info': grade_info
        }
        return chevron.render(template, html_params)

    if data['panel'] == 'submission':
        html_params = {
            'submission': True,
            'name': name,
            'uuid': pl.get_uuid(),
            'accesses': access_data,
            'score': score,
            'all_correct': correct,
            'all_incorrect': incorrect,
            'all_partial': partial,
            'show-partial-score': show_partial_score,
            'show-percentage-score': show_percentage_score,
            'feedback': data['feedback'].get(name, None),
        }
        return chevron.render(template, html_params)

    if data['panel'] == 'answer':
        html_params = {
            'answer': True,
            'name': name,
            'uuid': pl.get_uuid(),
            'accesses': access_data,
            'score': score,
        }
        return chevron.render(template, html_params)

def parse(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)
    
    name = pl.get_string_attrib(element, 'answers-name')

    empty_cache = pl.get_boolean_attrib(
        element, 'empty-cache', EMPTY_CACHE_DEFAULT
    )  # Default to False if not specified

    accesses = data['correct_answers'][name]

    for i in range(len(accesses)):
        if i == 0 and empty_cache == True:
            data['submitted_answers'][f'{name}{i}_hit'] = 'Miss'
            continue
        hit_miss = data['raw_submitted_answers'].get(f'{name}{i}_hit', None)
        if hit_miss == None:
            data['format_errors'][f'{name}{i}_hit'] = 'Must select a hit or miss'

    return
    
def grade(element_html: str, data: pl.QuestionData) -> None:
    element = lxml.html.fragment_fromstring(element_html)

    name = pl.get_string_attrib(element, 'answers-name')

    grade_mode = pl.get_string_attrib(element, 'grade-mode', GRADE_MODE_DEFAULT)
    weight = int(pl.get_string_attrib(element, 'weight', WEIGHT_DEFAULT))

    empty_cache = pl.get_boolean_attrib(
        element, 'empty-cache', EMPTY_CACHE_DEFAULT
    )  # Default to False if not specified

    accesses = data['correct_answers'][name]

    first_error = None
    num_correct = 0
    num_access = len(accesses)

    for i in range(num_access):
        if i == 0 and empty_cache == True:
            continue
        a_ans = 'Hit' if accesses[i]['hit'] else 'Miss'
        a_sub = data['raw_submitted_answers'].get(f'{name}{i}_hit', None)

        if a_ans == a_sub:
            data['partial_scores'][f'{name}{i}_hit'] = {
                'score': 1,
                'weight': 0,
            }
            num_correct += 1
        elif first_error == None and grade_mode == 'through-first':
            data['partial_scores'][f'{name}{i}_hit'] = {
                'score': 0,
                'weight': 0,
            }
            first_error = i
            break
        elif grade_mode != 'through-first':
            data['partial_scores'][f'{name}{i}_hit'] = {
                'score': 0,
                'weight': 0,
            }

    if first_error != None and grade_mode == 'through-first':
        data['feedback'][name] = f'Your first error was on access number {first_error}.'

    if empty_cache == True:
        num_access -= 1
    score = num_correct / num_access
    if grade_mode == 'all-or-nothing' and score < 1:
        score = 0

    data['partial_scores'][name] = {
        'score': score,
        'weight': weight,
    }

    return

def test(element_html: str, data: pl.ElementTestData) -> None:
    return