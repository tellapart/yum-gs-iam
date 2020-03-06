from google.auth import credentials
from google.auth import environment_vars
from google.cloud import storage

import logging
import os

import yum
import yum.config
import yum.Errors
import yum.plugins

from yum.yumRepo import YumRepository

URL_SCHEME = 'gs://'

__all__ = ['requires_api_version', 'plugin_type', 'CONDUIT',
           'config_hook', 'prereposetup_hook']

requires_api_version = '2.5'
plugin_type = yum.plugins.TYPE_CORE
CONDUIT = None
OPTIONAL_ATTRIBUTES = ['priority', 'base_persistdir', 'metadata_expire',
                       'skip_if_unavailable', 'keepcache', 'priority']
UNSUPPORTED_ATTRIBUTES = ['mirrorlist']

def config_hook(conduit):
  yum.config.RepoConf.google_application_credentials = yum.config.Option()
  yum.config.RepoConf.baseurl = yum.config.UrlListOption(
    schemes=('http', 'https', 's3', 'ftp', 'file', URL_SCHEME.strip(':/'))
  )


def check_base_url(baseurl):
  if len(baseurl) != 1:
    raise yum.plugins.PluginYumExit("Only one base url supported %",
        baseurl)


def parse_url(url):
  """Returns pair (bucket, path)
     Expects url in the format gs://<bucket>/<path>
  """
  if url.startswith(URL_SCHEME) and len(url) > len(URL_SCHEME):
    bucket_and_path = url.rstrip('/')[len(URL_SCHEME):].split('/', 1)
    if len(bucket_and_path) == 1:
      bucket_and_path.append('')
    return bucket_and_path
  return (None, None)


def replace_repo(repos, repo):
    repos.delete(repo.id)
    repos.add(GCSRepository(repo.id, repo))


def prereposetup_hook(conduit):
  """Plugin initialization hook. Setup the GCS repositories."""
  repos = conduit.getRepos()
  for repo in repos.listEnabled():
    if len(repo.baseurl) == 0:
        continue
    bucket, path = parse_url(repo.baseurl[0])
    if bucket and isinstance(repo, YumRepository):
      check_base_url(repo.baseurl)
      replace_repo(repos, repo)


class GCSRepository(YumRepository):

  def __init__(self, repoid, repo):
    super(GCSRepository, self).__init__(repoid)

    check_base_url(repo.baseurl)
    bucket, path = parse_url(repo.baseurl[0])

    if not bucket:
      msg = "gcsiam: unable to parse url %s'" % repo.baseurl
      raise yum.plugins.PluginYumExit(msg)

    self.baseurl = repo.baseurl

    if repo.google_application_credentials:
      os.environ[environment_vars.CREDENTIALS] = repo.google_application_credentials
    
    self.bucket = bucket
    self.base_path = path
    self.name = repo.name
    self.basecachedir = repo.basecachedir
    self.gpgcheck = repo.gpgcheck
    self.gpgkey = repo.gpgkey
    self.enablegroups = repo.enablegroups

    for attr in OPTIONAL_ATTRIBUTES:
      if hasattr(repo, attr):
        setattr(self, attr, getattr(repo, attr))

    for attr in UNSUPPORTED_ATTRIBUTES:
      if getattr(repo, attr):
        msg = "%s: Unsupported attribute: %s." % (__file__, attr)
        raise yum.plugins.PluginYumExit(msg)

    proxy = getattr(repo, 'proxy')
    if proxy not in [ '_none_', None, False ]:
        msg = "%s: Unsupported attribute: proxy. Set proxy=_none_ for an override or unset proxy." % (__file__)
        raise yum.plugins.PluginYumExit(msg)

    self.grabber = None
    self.enable()

  @property
  def urls(self):
    return self.baseurl
  @urls.setter
  def urls(self, value):
    pass


  @property
  def grabfunc(self):
    raise NotImplementedError("grabfunc called, when it shouldn't be!")


  @property
  def grab(self):
    if not self.grabber:
      self.grabber = GCSGrabber(self.bucket, self.base_path)
    return self.grabber


class GCSGrabber(object):

  def __init__(self, bucket, path):
    self.client = storage.Client()
    self.bucket = self.client.bucket(bucket)
    self.base_path = path
    self.verbose_logger = logging.getLogger("yum.verbose.plugin.GCSGrabber")

  def urlgrab(self, url, filename=None, **kwargs):
    """urlgrab(url) copy the file to the local filesystem."""
    blob_location = "%s/%s" % (self.base_path, url)
    self.verbose_logger.info("downloading gs://%s/%s to %s" % (self.bucket.name, blob_location, filename))
    url = url.lstrip('/')
    if not filename:
      filename = url

    blob = storage.blob.Blob(name=blob_location,bucket = self.bucket)
    blob.download_to_filename(filename)
    return filename
