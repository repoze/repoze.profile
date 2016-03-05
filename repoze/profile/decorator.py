import pstats

from repoze.profile.compat import profile as python_profile

def profile(title, sort_columns=('cumulative', 'time'), lines=20, stripdirs=True):
    def decorator(f):
        def wrapper(*args, **kw):
            profiler = python_profile.Profile()
            profiler.enable()
            result = profiler.runcall(f, *args, **kw)
            profiler.disable()
            stats = pstats.Stats(profiler)
            if stripdirs:
                stats.strip_dirs()
            stats.sort_stats(*sort_columns)
            print("-" * 80)
            print
            print(title)
            print("")
            if lines == 0:
                stats.print_stats()
            else:
                stats.print_stats(lines)
            print("")
            return result
        return wrapper
    return decorator
