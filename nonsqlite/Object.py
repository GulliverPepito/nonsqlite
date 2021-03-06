from nonsqlite import nonSQLiteClient
from json import dumps
from json import loads


class Object(object):
    _db         = None 
    _collection = None
    _db_name	= ''

    @classmethod
    def init(cls):
	if cls._db_name == '':
	    cls._db_name = 'Object.db'
	cls._db		= nonSQLiteClient(cls._db_name)
	cls._collection = cls._db.getCollection(cls.__name__)


    @classmethod
    def drop(cls):
	if cls._collection is None:
	    cls.init()
	cls._db.dropCollection(cls.__name__)


    @classmethod
    def checktype(cls, obj):
	if cls._collection is None:
	    cls.init()

	if (type(obj).__name__ != 'int'   and 
	    type(obj).__name__ != 'str'   and 
	    type(obj).__name__ != 'list'  and 
	    type(obj).__name__ != 'dict'  and 
	    type(obj).__name__ != 'float' and 
	    type(obj).__name__ != 'unicode' and
	    type(obj).__name__ != 'bool'):
	    return True
	else:
	    return False


    @staticmethod
    def sort(objlist, keytosort):
	if keytosort.startswith('-'):
	    keytosort = keytosort[1:]
	    return sorted(objlist, key=lambda k: k.__dict__[keytosort], reverse=True) 
	else:
	    return sorted(objlist, key=lambda k: k.__dict__[keytosort])

    @classmethod
    def filter(cls, query, limit=-1, sort=None):
	if cls._collection is None:
	    cls.init()

	key   = query.keys()[0]
	value = query[key]

	o, = value.__class__.__bases__
	if o.__name__ == 'Object':
	    query[key] = value.getid()

	ret = []
	element_list = cls._collection.find(query, limit)
	for element in element_list:
	    obj = cls.__load_document(element)
	    ret.append(obj)
	
	if sort is None:
	    return ret
	else:
	    return cls.sort(ret, sort)

    @classmethod
    def count(cls, query):
	if cls._collection is None:
	    cls.init()

	return cls._collection.count(query)


    @classmethod
    def len(cls):
	if cls._collection is None:
	    cls.init()

	return cls._collection.len()


    @classmethod
    def filterAND(cls, querylist=[], sort=None):
	if cls._collection is None:
	    cls.init()
	ret     = []
	objects = []
	for query in querylist:
	    objects.append(cls.filter(query))

	candidates = objects[0]
    
	if len(objects) == 1:
	    return candidates

	for c in candidates:
	    occurrence = 0
	    for o in objects[1:]:
		for obj in o:
		    if c.getid() == obj.getid():
			occurrence = occurrence + 1
			break

	    if occurrence == len(objects) - 1:
	        ret.append(c)

	if sort is None:
	    return ret
	else:
	    return cls.sort(ret, sort)

    @classmethod
    def filterOR(cls, querylist=[], sort=None):
	if cls._collection is None:
	    cls.init()
	ret     = []
	for query in querylist:
	    objects = cls.filter(query)
	    for o in objects:
		flag = False
		for r in ret:
		    if r.getid() == o.getid():
			flag = True
			break
		if not flag:
		    ret.append(o)

	if sort is None:
	    return ret
	else:
	    return cls.sort(ret, sort)



    @classmethod
    def like(cls, query, limit=-1, sort=None):
	if cls._collection is None:
	    cls.init()
	ret = []
	element_list = cls._collection.find(query, limit, True)
	for element in element_list:
	    obj = cls.__load_document(element)
	    ret.append(obj)


	if sort is None:
	    return ret
	else:
	    return cls.sort(ret, sort)

    @classmethod
    def dumps(cls):
	if cls._collection is None:
	    cls.init()

	ret = []
	element_list = cls._collection.all()
	for element in element_list:
	    ret.append(loads(element['document']))

	return dumps(ret)

    @classmethod
    def all(cls, sort=None):
	if cls._collection is None:
	    cls.init()

	ret = []
	element_list = cls._collection.all()
	for element in element_list:
	    obj = cls.__load_document(element)
	    ret.append(obj)
	
	if sort is None:
	    return ret
	else:
	    return cls.sort(ret, sort)

    @classmethod
    def getbyid(cls, oid):
	if cls._collection is None:
	    cls.init()
	ret = cls._collection.get(oid)
	if ret is not None:
	    return cls.__load_document(ret)

    @classmethod
    def get(cls, query):
	if cls._collection is None:
	    cls.init()

	key   = query.keys()[0]
	value = query[key]

	o, = value.__class__.__bases__
	if o.__name__ == 'Object':
	    query[key] = value.getid()

	ret = cls._collection.findOne(query)
	if ret != []:
	    return cls.__load_document(ret[0])


#    @classmethod
#    def fromJsonList(cls, jsonlist=[]):
#	for json in jsonlist:
#	    obj = cls.loads(json)
#	    obj.save()

    @classmethod
    def loads(cls, document):
	if cls._collection is None:
	    cls.init()

	json = loads(document)
	for doc in json:
	    element = {}
	    element['document'] = dumps(doc)
	    element['_id']      = None
	    obj = cls.__load_document(element)
	    obj.save()

    @classmethod
    def __load_document(cls, document):
	doc     = loads(document['document'])
	keys    = doc.keys()
	obj     = cls()
	obj._id = document['_id']

	# Si el objecto tiene atributos por definicion
	# Estos son los objectos "fuertemente tipados"
	objkeys  = vars(obj)
	for key in keys:
	    if key in objkeys:
	        if cls.checktype(obj.__dict__[key]):
		    o, = obj.__dict__[key].__class__.__bases__
		    if o.__name__ == 'Object':
		        obj.__dict__[key] = obj.__dict__[key].getbyid(doc[key])
		else:
		    #if type(obj.__dict__[key]).__name__ == 'list':
		    #	obj.__dict__[key].append(doc[key])
		    #else:
		    obj.__setattr__(key, doc[key])
	    else:
		obj.__setattr__(key, doc[key])
	return obj

    def __init__(self):
	self._id = None

    def getid(self):
	if '_id' in vars(self).keys():
	    return self._id
	return None

    def save(self):
	if self.__class__._collection is None:
	    self.__class__.init()

	fields = vars(self)
	keys   = fields.keys()

	if not '_id' in vars(self).keys():
	    self._id = None
	
	doc = {}
	
	for key in keys:
	    if key != '_id' and key != '_collection':
		if self.__class__.checktype(fields[key]):
		    o, = fields[key].__class__.__bases__
		    if o.__name__ == 'Object':
			doc[key] = fields[key].getid()
		else:
		    doc[key] = fields[key]

	if self._id is None:
	    ret = self.__class__._collection.insert(dumps(doc))
	    self._id = ret['object_id']
	else:
	    self.__class__._collection.update(self._id, dumps(doc))

    def delete(self):
	self.__class__._collection.deleteDocument(self._id)    
    

