import os
from fassembler.project import Project, Setting
from fassembler import tasks

class OpenCoreProject(Project):
    """
    Install OpenCore
    """

    name = 'opencore'
    title = 'Install OpenCore'

    settings = [
        Setting('opencore_repo',
                default='https://svn.openplans.org/svn/opencore/trunk',
                help='Repository for OpenCore'),
        Setting('featurelets_repo',
                default='https://svn.openplans.org/svn/topp.featurelets/trunk',
                help='Repository for topp.featurelets'),
        Setting('topp_utils_repo',
                default='https://svn.openplans.org/svn/topp.utils/trunk',
                help='Repository for topp.utils'),
        Setting('zope_instance',
                default='var/opencore/zope',
                help='Instance home for Zope'),
        Setting('zeo_instance',
                default='var/opencore/zeo',
                help='Instance home for ZEO'),
        Setting('zope_user',
                default='admin',
                help='Default admin username'),
        Setting('zope_password',
                ## FIXME: random?
                default='admin',
                help='Default admin password'),
        Setting('port',
                default='{{env.config.getint("general", "base_port")+int(config.port_offset)}}',
                help="Port to install Zope on"),
        Setting('port_offset',
                default='1',
                help='Offset from base_port for Zope'),
        Setting('host',
                default='localhost',
                help='Interface/host to serve Zope on'),
        Setting('zeo_port',
                default='{{env.config.getint("general", "base_port")+int(config.zeo_port_offset)}}',
                help="Port to install ZEO on"),
        Setting('zeo_port_offset',
                default='2',
                help='Offset from base_port for ZEO'),
        Setting('zeo_host',
                default='localhost',
                help='Interface/host to serve ZEO on'),
        Setting('zope_source',
                default='{{project.build_properties["virtualenv_path"]}}/src/Zope',
                help='Location of Zope source'),
        Setting('zope_svn_repo',
                default='http://svn.zope.de/zope.org/Zope/branches/2.9',
                help='Location of Zope svn'),
        ## FIXME: not sure if this is right:
        ## FIXME: should also be more global
        ## FIXME: also, type check on bool-ness
        Setting('debug',
                default='0',
                help='Whether to start Zope in debug mode'),
        Setting('email_confirmation',
                default='0',
                help='Whether to send email configuration'),
        ]

    files_dir = os.path.join(os.path.dirname(__file__), 'opencore-files')
    patch_dir = os.path.join(files_dir, 'patches')
    skel_dir = os.path.join(files_dir, 'zope_skel')

    actions = [
        tasks.VirtualEnv(),
        tasks.EasyInstall('Install PIL', 'PIL', find_links=['http://dist.repoze.org/simple/PIL/']),
        tasks.SvnCheckout('Check out Zope', '{{config.zope_svn_repo}}',
                          '{{config.zope_source}}'),
        tasks.Patch('Patch Zope', os.path.join(patch_dir, '*.diff'), '{{config.zope_source}}'),
        tasks.CopyDir('Create custom skel',
                      skel_dir, '{{project.name}}/src/Zope/custom_skel'),
        tasks.Script('Configure Zope', [
        './configure', '--prefix', '{{project.build_properties["virtualenv_path"]}}'],
        cwd='{{config.zope_source}}'),
        tasks.Script('Make Zope', ['make'], cwd='{{config.zope_source}}'),
        tasks.Script('Install Zope', ['make', 'inplace'], cwd='{{config.zope_source}}'),
        tasks.Script('Make Zope Instance', [
        'python', '{{config.zope_source}}/bin/mkzopeinstance.py', '--dir', '{{config.zope_instance}}',
        '--user', '{{config.zope_user}}:{{config.zope_password}}',
        '--skelsrc', '{{config.zope_source}}/custom_skel'],
                     use_virtualenv=True),
        tasks.Script('Make ZEO Instance', [
        'python', '{{config.zope_source}}/bin/mkzeoinstance.py', '{{config.zeo_instance}}', '{{config.zeo_port}}'],
                     use_virtualenv=True),
        tasks.SourceInstall('Install topp.utils',
                            '{{config.topp_utils_repo}}', 'topp.utils'),
        tasks.SourceInstall('Install topp.featurelets',
                            '{{config.featurelets_repo}}', 'topp.featurelets'),
        tasks.SourceInstall('Install opencore',
                            '{{config.opencore_repo}}', 'opencore'),
        ## FIXME: linkzope and linkzopebinaries?
        tasks.SaveURI(),
        ## FIXME: save ZEO uri too
        ]
