from pyqueen import TimeKit


def print_log(text):
    tk = TimeKit()
    print(tk.int2str(tk.now)+' '+str(text))