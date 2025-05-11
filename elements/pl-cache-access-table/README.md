# PrairieLearn OER Element: Cache Table Accesses

This element was developed by Geoffrey Herman. Please carefully test the element and understand its features and limitations before deploying it in a course. It is provided as-is and not officially maintained by PrairieLearn, so we can only provide limited support for any issues you encounter!

This element is designed to be used in parallel with the `pl-cache-table` element. If you like this element, you can use it in your own PrairieLearn course by copying the contents of the `elements` folder into your own course repository. We also recommend copying the `pl-cache-table` element and the `cache-tables.py` script from `serverFilesCourse` to help you display and generate caches to use with the element. After syncing, the element can be used as illustrated by the example question that is also contained in this repository.


## `pl-cache-table` element

This element displays a table that lists a series of memory access that interact with a cache. Students are expected to determine which memory accesses result in a hit or a miss in the cache. The element expects a correct answer to be stored in `data['correct_answers']` in a dictionary entry that shares the same `answers_name`. The dictionary entry should be a list of dictionary entries that include an address stored as a string and a hit/miss flag (`hit`).

```python 
data['correct_answers'][f'{answers_name}'] = [
    {'address': '0x1a', 'hit': False}, 
    {'address': '0x16', 'hit': False}, 
    {'address': '0x1f', 'hit': False}, 
    {'address': '0x1f', 'hit': True}
]
```

The element has 3 grading modes: `through-first` (default), `all`, and `all-or-nothing`. `through-first` is the default grading mode to discourage lazy guessing (i.e., students can guaranteed get all answers correct on a second guess without reasoning about the problem under the `all` grading condition)

### Example

<img src="example.png" width="300">

```html
<pl-cache-access-table 
    answers-name="{{params.answers_name}}_access" 
></pl-cache-access-table>
```

### Element Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `answers-name` | string (required) | Unique name for the element. |
| `grade-mode` | boolean (default: `through-first`) | If set to `through-first`, grading stops after the first mistake is encountered in the table and all remaining memory accesses are considered to be wrong. Students are not given feedback on later memory accesses. If set to `all`, each row is graded and feedback is available. For `through-first` and `all` the percentage score is the `number of correct rows` / `number of rows`. If set to `all-or-nothing`, each row is graded and feedback is available, but students get 0% unless all rows are correct. |
| `show-partial-score` | boolean (default: `true`) | Shows block-by-block feedback via highlighting in `blocks` or `all-or-nothing` grading mode and cell-by-cell feedback via highlighting in `cells`. |
| `show-percentage-score` | boolean (default: `true`) | Percentage score for the question is displayed as a badge. |
| `empty-cache` | boolean (default: 'false') | All cache blocks start as invalid, first access is a miss. Assert the first access is a miss with no radio button |
| `weight` | integer (default: `1`) | Weight to use when computing a weighted average score over elements. |
