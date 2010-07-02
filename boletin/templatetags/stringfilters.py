from htmlentitydefs import name2codepoint
import re

from django import template

register = template.Library()

entity_re = re.compile(r'&(?:amp;)?(?P<name>\w+);')


def _replace_entity(match):
    if match.group('name') in name2codepoint:
        return unichr(name2codepoint[match.group('name')])
    else:
        return "&%s;" % match.group('name')


@register.filter
def entity2unicode(value):
    """Convert HTML entities to their equivalent unicode character.

    Usage:

        {% load stringfilters %}
        {{ html_text_var|striptags|entity2unicode }}

    Borrowed from cmsutils (http://tracpub.yaco.es/cmsutils).

    """
    if value:
        return entity_re.sub(_replace_entity, value)
    else:
        return value
