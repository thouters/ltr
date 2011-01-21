from progressbar import *
import glib
import gio

class GioDownloader(object):
    def __init__(self, src,dst):
        self.loop = None
        self.src = src
        self.dst = dst
        self.pbar = False

    def start(self):
        self.mount()
        self.loop = glib.MainLoop()
        self.loop.run()


    def mount(self):
        self.mountoperation= gio.MountOperation()
        self.mountoperation.connect('ask-password', self.ask_password_cb)
        self.src.mount_enclosing_volume(self.mountoperation, self.srcmount_done_cb)

    def ask_password_cb(op, message, default_user, default_domain, flags):
        raise Exception, "Authentication not implemented"
        self.mountoperation.set_username(USERNAME)
        self.mountoperation.set_domain(DOMAIN)
        self.mountoperation.set_password(PASSWORD)
        self.mountoperation.reply(gio.MOUNT_OPERATION_HANDLED)

    def srcmount_done_cb(self, obj, res):
        try:
            obj.mount_enclosing_volume_finish(res)
        except gio.Error:
            pass

        self.mountoperation= gio.MountOperation()
        self.mountoperation.connect('ask-password', self.ask_password_cb)
        self.dst.mount_enclosing_volume(self.mountoperation, self.dstmount_done_cb)

    def dstmount_done_cb(self, obj, res):
        try:
            obj.mount_enclosing_volume_finish(res)
        except gio.Error:
            pass
        self.startdownload()

    def startdownload(self):
        print 'Downloading %s -> %s' % (self.src.get_basename(), self.dst.get_basename())
        info = self.src.query_info(gio.FILE_ATTRIBUTE_STANDARD_SIZE)
        self.total = info.get_attribute_uint64(gio.FILE_ATTRIBUTE_STANDARD_SIZE)


        self.src.copy_async(self.dst,\
                            self.finished_callback,\
                            flags=gio.FILE_COPY_OVERWRITE,\
                            progress_callback = self.progresscallback)

    def progresscallback(self,current_num_bytes,total_num_bytes):
        if not self.pbar:
            widgets = [self.src.get_basename(), Percentage(), ' ', Bar(marker=RotatingMarker()),
                   ' ', ETA(), ' ', FileTransferSpeed()]
            self.pbar = ProgressBar(widgets=widgets, maxval=total_num_bytes).start()
        self.pbar.update(current_num_bytes)

    def finished_callback(self,f, userdata):
        print "finished!"
        self.stop()

    def stop(self):
        if self.pbar:
            self.pbar.finish()
        self.loop.quit()

def main(args):
    from sys import argv
    src = gio.File(argv[1])
    dst = gio.File(argv[2])
    GioDownloader(src,dst).start()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
