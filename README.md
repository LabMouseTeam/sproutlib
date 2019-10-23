[![Build Status](https://travis-ci.com/LabMouseTeam/sproutlib.svg?branch=master)](https://travis-ci.com/LabMouseTeam/sproutlib) [![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=LabMouseTeam_sproutlib&metric=security_rating)](https://sonarcloud.io/dashboard?id=LabMouseTeam_sproutlib) [![Bugs](https://sonarcloud.io/api/project_badges/measure?project=LabMouseTeam_sproutlib&metric=bugs)](https://sonarcloud.io/dashboard?id=LabMouseTeam_sproutlib) [![Package Vulnerabilities](https://snyk.io/test/github/LabMouseTeam/sproutlib/badge.svg)](https://snyk.io/test/github/LabMouseTeam/sproutlib)

# Sproutlib

Release: 2.0.0

<div align="center">
	<img src="https://github.com/LabMouseTeam/sproutlib/tree/master/logo/sproutlib.gif">
</div>

Sproutlib is a set of python3 classes that enable *infrastructure as code* in
a new, dynamic microservice model.

Instead of defining configuration files that *describe* how services should
run, services composed of object oriented classes are instantiated *from*
configuration data.

This allows for more direct relationship between YAML and executable code
by directly coupling YAML to variables that control each layer of an object
oriented microservice.

As a result, Sproutlib also serves as a way to safely serialize objects
across a transport, allowing for a single microservice configuration to be
spawned across N nodes with a single queue write operation. What's elegant
about the Sproutlib model for spawning similar microservices is that the
service itself can render itself as a string, which will be valid JSON. This
enables each microservice to clone its specific configuration instantly
without additional work.

# Usage
First, create an object that is based on any object tree you like, but is
rooted at labmouse.sproutlib.SproutSchema

Next, create SproutSchema objects as subclasses. The SproutSchema classes
define a namespace that will be used as configuration keys in the corresponding
YAML or JSON configuration.

```
class Foo(SproutSchema):
    class bar(SproutSchema):
        required = True
        strict = True
    class baz(SproutSchema):
        type = int

    ...
```

This class can now be instantiated using a Python dict, YAML configuration
string, or a JSON string. For example, the following Python dict and YAML
string contains the same information:

YAML:
```
bar: 'i am a bar'
baz: 42
```

JSON:
```
{'bar': 'i am a bar', 'baz': 42}
```

and the above class *Foo* can be instantiated with either one with the same
result:
```
y = """bar: 'i am a bar'\nbaz: 42"""
f = Foo(y)

d = {'bar': 'i am a bar', 'baz': 42}
f = Foo(d)
```

Complex classes can even be created to make it easier to contain information
to a specific namespace (or set of namespaces). 
```
class Bar(SproutSchema):
    class bar1(SproutSchema):
        type = int
        strict = True

    class bar2(SproutSchema):
        type = float
        strict = True


class Foo(Bar, Thread):
    class foo1(SproutSchema):
        pass

    class foo2(SproutSchema):
        pass

    def __init__(self, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)
        Thread.__init__(self)

    def run(self):
        ... do a thread thing here ...


if __name__ == "__main__":
    f = Foo('''...data...''')
    f.start()
    ...
```

## Type
The 'type' parameter dictates what type of data should be stored at this
namespace. It can be any Python type or custom Python class.

## Required
The 'required' parameter dictates whether the namespace is included as
output even if it were never set. For example, when creating a schema
to interact with a remote API, you may not want (or need) to set all
parameters in the API call. However, the API call may require the presence
of the name. 'required' ensures that the name will always appear when the
string version of the object is generated, helping guarantee that the
remote API will never raise an exception because of a missing parameter.

For example, in the above class, if we did:
```
f = Foo()
f['baz'] = 127
api_call['foo'] = str(f)
```

The following would be sent via JSON to the remote API:
```
{'foo': {"bar": "","baz": 127}}
```

This makes it faster and simpler to both generate API schemas and interact
with the remote endpoint.

## Strict
The 'strict' keyword ensures that the type of object used in a set on the
schema namespace adheres to the 'type' parameter. If it does not, a
SproutStrictTypeException is raised.

## Subtype
For lists or similar python constructs, where a facet of the primary object
can be any type, the facet itself may be strictly checked. This is done by
setting the subtype.

It is also necessary to set the subtype so the get action can interpret the
data within the facet correctly. This is especially necessary when a custom
class has been placed within a list, for example, and we're converting JSON
to actual objects. The 'get' action will convert the name to the appropriate
type seamlessly and transparently.

## Hidden
This parameter hides a particular namespace during the string generation
process. This option is deprecated in favor of simply using a class or
instance variable that does not inherit the SproutSchema base class.

# Validation
For validation, Lab Mouse suggests the use of a modern schema validation tool
such as the @23andMe Yamale utility.
https://github.com/23andMe/Yamale

This tool can help you define not only the YAML configuration files for your
project, but how your objects should be defined within your microservice as
you compose your code.

# Thanks
Thanks to pixelrogueart for creating our custom logo. Check him out on
Instagram here: [@pixelrogueart](https://www.instagram.com/pixelrogueart/)

# License
Sproutlib uses the GNU General Public License v3.0.
