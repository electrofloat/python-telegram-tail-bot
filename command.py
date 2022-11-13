import logging
import shlex
from stats import Stats
from config import Config

try:
    from telegram import Update
    from telegram import ParseMode
    from telegram.ext import CallbackContext
except ImportError:
    print("ERROR: install ptb manually: sudo pip install python-telegram-bot --upgrade")
    sys.exit(2)

class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pttb.command')
logger.addHandler(NullHandler())

class Command():
    def __init__(self, command):
        self.command = command
        self.subcommands = {}

    def __str__(self):
        return self.command

    def add_subcommand(self, subcommand):
        self.subcommands[str(subcommand)] = subcommand

    def process(self, message):
        argv = shlex.split(message)
        logging.info("text: %s" % argv)
        argv.pop(0)

        if len(argv) == 0:
            return self.process_command()

        subcommand = argv.pop(0)
        if str(subcommand) in self.subcommands:
            return self.subcommands[str(subcommand)].process(argv)

        return self.show_usage()

    def process_command(self):
        raise NotImplementedError

    def show_usage(self):
        raise NotImplementedError

    def get_short_description(self):
        raise NotImplementedError

    def handler(self, update: Update, context: CallbackContext):
        msg = "Internal error"
        if update.message:
            msg = self.process(update.message.text)
        elif update.edited_message:
            msg = self.process(update.edited_message.text)

        context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML)

class SubCommand():
    def __init__(self, subcommand):
        self.subcommand = subcommand

    def __str__(self):
        return self.subcommand

    def process(self, message):
        raise NotImplementedError

class SubCommandTriggerAdd(SubCommand):
    def __init__(self):
        SubCommand.__init__(self, "add")

    def process(self, argv):
        msg = ""
        if len(argv) != 3:
            msg = ""
            msg += "Usage: \n"
            msg += "<code>/trigger add '&lt;regex&gt;' &lt;duration&gt; '&lt;message&gt;'</code> - Add a new trigger with a quoted regular expression with a coalesce duration in seconds (may be 0), and a quoted message\n"
            return msg

        regexp = argv.pop(0)
        duration = argv.pop(0)
        message = argv.pop(0)
        if not Config.validate_duration(duration):
            return "Error: Expecting second argument as a number\n"
        ret, retmsg = Config.trigger_add(regexp, duration, message)
        if not ret:
            msg = "Error: %s\n" % retmsg
        else:
            #Config.write()
            msg = "Success: %s\n" % retmsg

        return msg

class SubCommandTriggerDel(SubCommand):
    def __init__(self):
        SubCommand.__init__(self, "del")

    def process(self, argv):
        msg = ""
        if len(argv) != 1:
            msg = "Usage: \n"
            msg += "<code>/trigger del &lt;idx&gt;</code> - Remove a trigger by its listed index\n"

            return msg

        index = argv.pop(0)
        if not index.isnumeric():
            return "Error: Expecting first argument as a number\n"

        index = int(index)
        ret, retmsg = Config.trigger_del(index)
        if not ret:
            msg += "Error: %s\n" % retmsg
        else:
            #Config.write()
            msg += "Success: %s\n" % retmsg

        return msg

class CommandTrigger(Command):
    def __init__(self):
        Command.__init__(self, "trigger")
        self.add_subcommand(SubCommandTriggerAdd())
        self.add_subcommand(SubCommandTriggerDel())

    def process_command(self):
        triggers = Config.trigger_list()
        msg = "%d trigger(s) follow:\n" % len(triggers)
        msg += "<pre>\n"
        idx = 0
        for t in triggers:
            msg += "idx %d: \n" % idx
            msg += "  * regexp='%(regexp)s'\n  * duration=%(duration)s\n  * message='%(message)s'\n" % t
            idx += 1
        msg += "</pre>\n"

        return msg

    def show_usage(self):
        msg = "Usage: \n"
        msg += "<code>/trigger</code> - List triggers\n"
        msg += "<code>/trigger add '&lt;regex&gt;' &lt;duration&gt; '&lt;message&gt;'</code> - Add a new trigger with a quoted regular expression with a coalesce duration in seconds (may be 0), and a quoted message\n"
        msg += "<code>/trigger del &lt;idx&gt;</code> - Remove a trigger by its listed index\n"

        return msg

    def get_short_description(self):
        return "List triggers or use subcommands: add, del"

class CommandStats(Command):
    def __init__(self):
        Command.__init__(self, "stats")

    def process_command(self):
        msg = "<pre>%s</pre>" % Stats.get_stats()

        return msg

    def show_usage(self):
        msg = "Usage: \n"
        msg += "<code>/stats</code> - Show statistics"

        return msg

    def get_short_description(self):
        return "Show statistics"

class SubCommandSilenceAdd(SubCommand):
    def __init__(self):
        SubCommand.__init__(self, "add")

    def process(self, argv):
        msg = ""
        if len(argv) != 2:
            msg = ""
            msg += "Usage: \n"
            msg += "<code>/silence add '&lt;idx&gt;' &lt;duration&gt;</code> - Silence the &lt;idx&gt; trigger for &lt;duration&gt; duration\n"
            return msg

        idx = argv.pop(0)
        if not idx.isnumeric():
            return "Error: Expecting first argument as a number\n"
        idx = int(idx)
        if idx < 0 or idx >= len(Config.yaml['triggers']):
            return "Error: trigger idx is out of range (0..%d)" % (len(Config.yaml['triggers']) - 1)
        duration = argv.pop(0)
        if not Config.validate_duration(duration):
            return "Error: Expecting second argument as a duration\n"
        ret, retmsg = Config.silence_add(idx, duration)
        if not ret:
            msg = "Error: %s\n" % retmsg
        else:
            #Config.write()
            msg = "Success: %s\n" % retmsg

        return msg

class SubCommandSilenceDel(SubCommand):
    def __init__(self):
        SubCommand.__init__(self, "del")

    def process(self, argv):
        msg = ""
        if len(argv) != 1:
            msg = "Usage: \n"
            msg += "<code>/silence del &lt;idx&gt;</code> - Remove a silence by its listed index\n"

            return msg

        index = argv.pop(0)
        if not index.isnumeric():
            return "Error: Expecting first argument as a number\n"

        index = int(index)
        ret, retmsg = Config.silence_del(index)
        if not ret:
            msg += "Error: %s\n" % retmsg
        else:
            #Config.write()
            msg += "Success: %s\n" % retmsg

        return msg

class CommandSilence(Command):
    def __init__(self):
        Command.__init__(self, "silence")
        self.add_subcommand(SubCommandSilenceAdd())
        self.add_subcommand(SubCommandSilenceDel())

    def process_command(self):
        silences = Config.silence_list()
        msg = "%d silence(s) follow:\n" % len(silences)
        msg += "<pre>\n"
        idx = 0
        for t in silences:
            msg += "idx %d: \n" % idx
            msg += "  * trigger_idx='%(idx)s'\n  * duration=%(duration)s\n" % t
            idx += 1
        msg += "</pre>\n"

        return msg

    def show_usage(self):
        msg = "Usage: \n"
        msg += "<code>/silence</code> - List silences\n"
        msg += "<code>/silence add '&lt;idx&gt;' &lt;duration&gt;</code> - Silence the &lt;idx&gt; trigger for &lt;duration&gt; duration\n"
        msg += "<code>/silence del &lt;idx&gt;</code> - Remove a silence by its listed index\n"

        return msg

    def get_short_description(self):
        return "List silences or use subcommands: add, del"
