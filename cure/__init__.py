import builtins
import copy
import inspect
import keyword
import sys
import types
from functools import update_wrapper
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union, cast  # noqa

from decorator import FunctionMaker  # , decorate

from .__version__ import __version__, __version_info__  # noqa

__author__ = "Carl Oscar Aaro"
__email__ = "hello@carloscar.com"

respected_keywords: set = set(dir(builtins)) | set(keyword.kwlist)


def decorate(func, caller):
    if not func:
        raise TypeError("'cure.decorator' must decorate a callable")

    bound_arg = ()
    is_staticmethod = False
    is_classmethod = False
    if not isinstance(func, types.FunctionType) and isinstance(func, staticmethod):
        func = func.__func__
        is_staticmethod = True
    elif not isinstance(func, types.FunctionType) and isinstance(func, classmethod):
        func = func.__func__
        is_classmethod = True
    elif not isinstance(func, types.FunctionType) and getattr(func, "__func__", None) and getattr(func, "__self__", None) and inspect.ismethod(func):
        bound_arg = (getattr(func, "__self__"),)
        func = func.__func__

    name = None
    if inspect.isfunction(func):
        name = func.__name__ if not func.__name__ == '<lambda>' else '_lambda_'
    if not name:
        name = "_decorated_function_"

    signature = f"{name}(*args, **kwargs)"

    if inspect.isgeneratorfunction(caller):
        result = FunctionMaker.create(
            signature, "for result in _call_(_func_, *args, **kwargs): yield result", {"_call_": caller, "_func_": func}, __wrapped__=func)
    else:
        result = FunctionMaker.create(
            signature, "return _call_(_func_, *args, **kwargs)",
            {"_call_": caller, "_func_": func}, __wrapped__=func)

    if hasattr(func, '__qualname__'):
        result.__qualname__ = func.__qualname__

    if bound_arg:
        result = result.__get__(bound_arg[0])
    if is_staticmethod:
        result = staticmethod(result)
    if is_classmethod:
        result = classmethod(result)

    return result


def trail_name(kw: str) -> str:
    if kw in respected_keywords:
        return f"{kw}_"
    return kw


def _cure(func: Callable, options: List, *args: Any, **kwargs: Any) -> Any:
    trailed_kwargs = {trail_name(k): v for k, v in kwargs.items()}
    return func(*args, **trailed_kwargs)


def cure_decorator(*pargs: Any, **pkwargs: Any) -> Callable:
    options = []

    def caller(*args: Any, **kwargs: Any):
        try:
            func, *args = args
        except ValueError:
            raise TypeError("'cure.decorator' must decorate a callable")

        return _cure(func, options, *args, **kwargs)

    decorator = FunctionMaker.create(
        '_decorator_wrapper_(*f)',
        'if not f: return _decorate_(None, _call_)\n'
        'return _decorate_(f[0], _call_)',
        {"_call_": caller, "_decorate_": decorate}, module=caller.__module__, __wrapped__=caller)

    if pargs and not pkwargs and len(pargs) == 1 and (callable(pargs[0]) or (isinstance(pargs[0], (staticmethod, classmethod)) and not isinstance(pargs[0], types.FunctionType))):
        result = decorator(pargs[0])
    else:
        result = decorator

    return result


class CureDecorator(object):
    def __init__(self, func):
        self.func = func
        update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        result = self.func(*args, **kwargs)
        if getattr(result, "__qualname__", None) == "_decorator_wrapper_":
            return CureDecorator(result)
        return result

    def __repr__(self):
        id_ = hex(id(self))
        return f"<cure.decorator at {id_}>"


class Cure(object):
    __version__: str = __version__
    __version_info__: Tuple[int, int, int] = __version_info__
    __author__: str = __author__
    __email__: str = __email__

    def __init__(self):
        self.decorator = CureDecorator(cure_decorator)
        self.cure = self.decorator

        self.respected_keywords = respected_keywords
        self.trail_name = trail_name

        update_wrapper(self, cure_decorator)

    def __call__(self, *args, **kwargs):
        result = cure_decorator(*args, **kwargs)
        if getattr(result, "__qualname__", None) == "_decorator_wrapper_":
            return CureDecorator(result)
        return result

    def __repr__(self):
        id_ = hex(id(self))
        return f"<cure.decorator at {id_}>"

#setattr(cure_decorator, "__repr__", cure_repr)
#setattr(cure_decorator, "__str__", cure_repr)

#cure = copy.deepcopy(cure_decorator)

#cure.__version__: str = __version__
#cure.__version_info__: Tuple[int, int, int] = __version_info__
#cure.__author__: str = __author__
#cure.__email__: str = __email__

#cure.decorator = cure_decorator

#cure.trail_name = trail_name

cure = Cure()
sys.modules[__name__] = cure  # type: ignore