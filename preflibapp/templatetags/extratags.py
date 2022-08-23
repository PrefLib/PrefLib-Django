from django import template

register = template.Library()


@register.filter
def key_value(d, key):
    return d.get(key)


@register.filter
def get_prop_from_file(query_set, metadata):
    return query_set.get(metadata=metadata)
