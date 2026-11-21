"""Fail-closed, source-proven location adapter; no broad string substitutions."""
import argparse, pathlib
TARGET = pathlib.Path('src/MEGASync/MegaApplication.cpp')
NEEDLE = '    QStringList dataPaths = QStandardPaths::standardLocations(QStandardPaths::AppLocalDataLocation);'
INSERT = '''    // Community portable build: the launcher supplies an absolute, owned Data path.
    // Restrict folder permissions with MEGA's native security routine, just as for
    // the normal Windows local-appdata location. No installed profile is imported.
#ifdef Q_OS_WIN
    const QString portableDataDir = qEnvironmentVariable("MEGA_PORTABLE_DATA_DIR");
    if (!portableDataDir.isEmpty())
    {
        const QDir location(portableDataDir);
        if (!location.isAbsolute())
        {
            qFatal("MEGA_PORTABLE_DATA_DIR must be absolute");
        }
        dataPath = QDir::toNativeSeparators(QDir::cleanPath(portableDataDir));
        dataPathFromStandardLocation = true;
        Platform::getInstance()->createFolderRestrictedToOwner(dataPath, &dataPathCreationError);
        return;
    }
#endif
'''
def patch(root: pathlib.Path):
    p = root / TARGET
    if not p.is_file(): raise SystemExit(f'Upstream source missing: {p}')
    src = p.read_text(encoding='utf-8-sig')
    if src.count(NEEDLE)!=1: raise SystemExit(f'Expected exactly one known source anchor, got {src.count(NEEDLE)}; refuse to patch version')
    if 'MEGA_PORTABLE_DATA_DIR' in src: raise SystemExit('Source already patched or upstream has new native support; inspect manually')
    if 'void MegaApplication::loadDataPath()' not in src or 'createFolderRestrictedToOwner' not in src: raise SystemExit('Upstream data-path/security contract changed')
    result = src.replace(NEEDLE, INSERT + NEEDLE, 1)
    p.write_text(result,encoding='utf-8',newline='\n')
    print('SOURCE-INSPECTED ADAPTER APPLIED:',p)
if __name__=='__main__':
    x=argparse.ArgumentParser();x.add_argument('source_root',type=pathlib.Path);patch(x.parse_args().source_root)
