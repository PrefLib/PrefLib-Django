from django import template

register = template.Library()

@register.filter
def keyvalue(d, key):    
	return d.get(key)

@register.filter
def getPropFromFile(querySet, metadata):
	return querySet.get(metadata = metadata) 