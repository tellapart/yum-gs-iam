# yum-gs-iam

This is a [yum](http://yum.baseurl.org/) plugin that allows for
private Google Cloud Storage buckets to be used as package repositories. The plugin
utilizes Google's [Cloud Identity and Access Management](https://cloud.google.com/iam/)
(IAM) for authorization.

## How to set it up

### Setup the repository
You should be familiar with how yum works in general.

* If you want to use an internal Google bucket to host an internal mirror of a public
repository (e.g. CentOS Core, EPEL, ...), simply rsync the repository to a local temp directory
(check out [Create Local Mirrors for Updates and Installs](https://wiki.centos.org/HowTos/CreateLocalMirror))
and then use [gsutil's rsync](https://cloud.google.com/storage/docs/gsutil/commands/rsync) to push it to your bucket.

* If you want to create an internal repository for internal packages use [createrepo](http://yum.baseurl.org/wiki/RepoCreate)
to create a repository in a local temp directory and push it to the bucket using `gsutil`
or what ever other mechanism you like.

Permission the bucket to be readable by all [service accounts](https://cloud.google.com/compute/docs/access/service-accounts)
that you want to have access. If the machines accessing the yum repository are running inside of [Googles Compute Engine](https://cloud.google.com/compute/)
and your setup is not very complicated, you probably want to give read permissions to the
[Compute Engine default service account](https://cloud.google.com/compute/docs/access/service-accounts#compute_engine_default_service_account).

### Install the plugin

Generate a RPM for the plugin. If you have [Docker](https://www.docker.com/) running, simply run `./make_rpm_docker.sh`. If you don't run Docker, you can make the rpm by running:
```bash
sudo yum groupinstall -y 'Development Tools'
sudo yum install -y ruby-devel tar wget rpm which
sudo gem install fpm
./make_rpm.sh
```
This will place the plugin rpm in your current directory.

Now you can install the plugin on the machines that need access to the repo by:

1. Install Google's Cloud Storage python library, `pip install --upgrade google-cloud-storage`
2. Install the plugin, e.g.: `yum install -y yum-plugin-gs-iam-*.rpm`
3. The plugin depends on the google cloud and auth python libraries being installed `pip install google.auth google.cloud`

You ready to configure your `.repo` file, check out the [example.repo](example.repo).


In short, the `baseurl` parameter in your `.repo` file is expected to be in the format: `gs://<bucket>/<path to repo>`
where `<path to repo>` is optional.


This plugin uses the [Google Application Default Credentials](https://developers.google.com/identity/protocols/application-default-credentials).
This means, if you are running in GCE and your machine service account it read permissioned, you will not have to supply any credentials in your `.repo` file.
