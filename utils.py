#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supporting funcitons to the game Cartolan

@author: tom
"""

def replace_references(old_reference, new_reference, subject, memo, valid_classes):
    '''Recursively crawls the graph of an object's attributes, replacing memory references to one object with those for another
    
    Arguments:
    old_reference the memory reference to replace
    new_reference the memory reference to replace it with
    subject takes an object, to recursively delve into replacing references
    memo takes a list of subjects that have been crawled so far
    '''
#    print("Replacing references in "+str(subject))
    if old_reference.__class__ != new_reference.__class__:
#        print("not going to try and replace references to a different data structure")
        return False 
    elif subject in memo:
#        print(str(subject)+" has been / is being investigated already, so stopping recursion")
        return False 
    elif any([isinstance(subject, valid_class) for valid_class in valid_classes]):
        memo.append(subject) #Remember that this object has been / is being explored elsewhere in the recursion
        for attribute_name in dir(subject):
            attribute = getattr(subject, attribute_name)
            if isinstance(attribute, list):
#                print("Checking all the elements of a list attribute, "+str(attribute)+", for "+str(subject)+" to replace and otherwise dig into them a step further")
                for new_subject in attribute:
                    if id(old_reference) == id(new_subject):
                        print("Found an instance of "+str(old_reference)+" in "+str(subject)+"'s "+str(attribute_name)+" list and replaced with "+str(new_reference))
                        old_ref_idx = attribute.index(old_reference)
                        attribute.pop(old_ref_idx)
                        attribute.insert(old_ref_idx, new_reference)
                    else:
#                        print("Exploring a step futher into the object hierarchy, through "+str(new_subject))
                        replace_references(old_reference, new_reference, new_subject, memo, valid_classes)
            elif isinstance(attribute, dict):
#                print("Checking all the elements of a dict attribute, "+str(attribute)+", for "+str(subject)+" to replace and otherwise dig into them a step further")
                for key in attribute:
                    new_subject = attribute[key]
                    if id(old_reference) == id(new_subject):
                        print("Found an instance of "+str(old_reference)+" in "+str(subject)+"'s "+str(attribute_name)+" dict and replaced with "+str(new_reference))
                        attribute.pop(key)
                        attribute[key] = new_reference
                    else:
#                        print("Exploring a step futher into the object hierarchy, through "+str(new_subject))
                        replace_references(old_reference, new_reference, new_subject, memo, valid_classes)
            elif not callable(attribute): #exclude methods, but deal with all other data structures
#                print("Directly comparing for replacement the "+str(attribute)+" attribute of "+str(subject))
                if id(old_reference) == id(attribute):
                    print("Found an instance of "+str(old_reference)+" in "+str(subject)+" and replaced with "+str(new_reference))
                    setattr(subject, attribute_name, new_reference)
                else:
                    new_subject = attribute
#                    print("Exploring a step futher into the object hierarchy, through "+str(new_subject))
                    replace_references(old_reference, new_reference, new_subject, memo, valid_classes)
        return True
#    else:
#        print(str(subject)+"'s class "+str(subject.__class__)+" was not an instance of the valid classes, so not recursing any deeper.")
    return False