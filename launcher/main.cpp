// Community-built launcher. Never changes installed-app settings, registry, or shortcuts.
// MEGA's application data directory is patched in upstream MegaApplication.cpp to obey
// MEGA_PORTABLE_DATA_DIR, validated and supplied before CreateProcessW.
#include <windows.h>
#include <tlhelp32.h>
#include <shellapi.h>
#include <string>
#include <vector>
#include <cwctype>

// Only our child MEGAsync process inherits these Qt cache settings.
// Do NOT redirect LOCALAPPDATA/APPDATA: that would also affect other Windows APIs.


static void Error(const wchar_t* msg) { MessageBoxW(nullptr, msg, L"MEGA Desktop Community Portable", MB_ICONERROR | MB_OK); }
static std::wstring ExePath() {
    std::vector<wchar_t> buf(512);
    for (;;) {
        DWORD n=GetModuleFileNameW(nullptr,buf.data(),static_cast<DWORD>(buf.size()));
        if (!n) return {};
        if(n < buf.size()-1) return std::wstring(buf.data(),n);
        if(buf.size()>32768) return {};
        buf.resize(buf.size()*2);
    }
}
static bool ExistsFile(const std::wstring& p) {
    DWORD a=GetFileAttributesW(p.c_str()); return a != INVALID_FILE_ATTRIBUTES && !(a & FILE_ATTRIBUTE_DIRECTORY);
}
static bool IsRealDirectory(const std::wstring& p) {
    DWORD a=GetFileAttributesW(p.c_str()); return a != INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_DIRECTORY) && !(a & FILE_ATTRIBUTE_REPARSE_POINT);
}
static bool Mkdir(const std::wstring& p) { return CreateDirectoryW(p.c_str(),nullptr) || (GetLastError()==ERROR_ALREADY_EXISTS && IsRealDirectory(p)); }
static bool IsSupportedFilesystem(const std::wstring& path) {
    wchar_t root[MAX_PATH]={0}, fs[MAX_PATH]={0};
    if(!GetVolumePathNameW(path.c_str(),root,MAX_PATH)) return false;
    if(!GetVolumeInformationW(root,nullptr,0,nullptr,nullptr,nullptr,fs,MAX_PATH)) return false;
    return _wcsicmp(fs,L"NTFS")==0 || _wcsicmp(fs,L"ReFS")==0;
}
static bool OtherMegaRunning() {
    HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);
    if(s==INVALID_HANDLE_VALUE) return true; // fail closed
    PROCESSENTRY32W e{}; e.dwSize=sizeof(e);
    bool found=false;
    if(Process32FirstW(s,&e)) do {
        if(_wcsicmp(e.szExeFile,L"MEGAsync.exe")==0) { found=true; break; }
    } while(Process32NextW(s,&e));
    CloseHandle(s); return found;
}
static std::wstring Quote(const std::wstring& s) {
    std::wstring q=L"\""; unsigned backslash=0;
    for(wchar_t c:s) {
        if(c==L'\\') { ++backslash; continue; }
        if(c==L'\"') { q.append(backslash*2+1,L'\\'); q+=L'\"'; backslash=0; continue; }
        q.append(backslash,L'\\'); backslash=0; q+=c;
    }
    q.append(backslash*2,L'\\'); return q+L"\"";
}
// Qt 5.15 QML_DISK_CACHE_PATH uses QString::fromLocal8Bit(qgetenv(...)).
// A non-ASCII portable root might not survive the Windows active code page.
// In that situation, disable just the optional QML disk cache, never fall
// back to creating host-local files or create a lossy directory name.
static bool IsAsciiPath(const std::wstring& path) {
    for (wchar_t c : path) if (c > 0x7f) return false;
    return true;
}
static bool UnsetEnv(const wchar_t* key) {
    if (SetEnvironmentVariableW(key, nullptr)) return true;
    return GetLastError() == ERROR_ENVVAR_NOT_FOUND;
}
static bool SetPortableQtCaches(const std::wstring& data) {
    // These are documented Qt process-local switches (not Windows-wide env).
    // They prevent Qt 5 OpenGL and future Qt 6 RHI shader disk caches from
    // writing into shared %LOCALAPPDATA%\cache\qtshadercache-*.
    if (!SetEnvironmentVariableW(L"QT_DISABLE_SHADER_DISK_CACHE", L"1")) return false;
    if (!SetEnvironmentVariableW(L"QSG_RHI_DISABLE_SHADER_DISK_CACHE", L"1")) return false;

    const std::wstring qmlCache = data + L"\\Cache\\QML";
    // Qt 5.15 decodes QML_DISK_CACHE_PATH with the local code page; be
    // conservative for Unicode and extreme paths until real-runtime proven.
    if (!IsAsciiPath(qmlCache) || qmlCache.size() >= 240) {
        return UnsetEnv(L"QML_FORCE_DISK_CACHE")
            && UnsetEnv(L"QML_DISK_CACHE_PATH")
            && SetEnvironmentVariableW(L"QML_DISABLE_DISK_CACHE", L"1");
    }
    const std::wstring cacheRoot = data + L"\\Cache";
    if (!Mkdir(cacheRoot) || !IsRealDirectory(cacheRoot)
        || !Mkdir(qmlCache) || !IsRealDirectory(qmlCache)) return false;
    // QML cache remains enabled and reusable across launches and relocation.
    // An inherited QML_DISABLE_DISK_CACHE=1 is intentionally respected.
    return SetEnvironmentVariableW(L"QML_DISK_CACHE_PATH", qmlCache.c_str());
}
int WINAPI wWinMain(HINSTANCE,HINSTANCE,LPWSTR,int) {
    std::wstring path=ExePath();
    auto slash=path.find_last_of(L"\\/");
    if(path.empty() || slash==std::wstring::npos) {Error(L"Unable to determine executable location.");return 1;}
    std::wstring root=path.substr(0,slash);
    std::wstring app=root+L"\\App\\MEGAsync";
    std::wstring exe=app+L"\\MEGAsync.exe";
    std::wstring data=root+L"\\Data";
    std::wstring profile=data+L"\\MEGAsync";
    if(!ExistsFile(exe) || !IsRealDirectory(app)) {Error(L"Packaged MEGAsync.exe is missing or App directory is unsafe.");return 2;}
    if(!IsSupportedFilesystem(root)) {
        Error(L"Portable credentials require an NTFS/ReFS volume. FAT/exFAT are not supported by this protective launcher.");return 3;
    }
    if(!Mkdir(data) || !IsRealDirectory(data) || !Mkdir(profile) || !IsRealDirectory(profile)) {
        Error(L"Unable to create safe portable Data directory. Junctions and symbolic links are not allowed.");return 4;
    }
    if(OtherMegaRunning()) {
        Error(L"MEGAsync is already running. Exit the installed/other portable MEGA client from its tray first.");return 5;
    }
    // Upstream's patched loadDataPath() applies MEGA's restrictive, owner-only ACL routine.
    if(!SetEnvironmentVariableW(L"MEGA_PORTABLE_DATA_DIR",profile.c_str())) {Error(L"Cannot set portable profile path.");return 6;}
    if(!SetPortableQtCaches(data)) {
        Error(L"Cannot configure portable Qt caches safely. Check Data folder permissions.");return 9;
    }
    // No APPDATA/LOCALAPPDATA/TEMP rewriting or host cache deletion. Settings
    // affect only MEGAsync.exe and its descendants, never installed programs.
    int argc=0; LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    std::wstring cmd=Quote(exe);
    if(argv){for(int i=1;i<argc;i++){cmd+=L" ";cmd+=Quote(argv[i]);} LocalFree(argv);}
    std::vector<wchar_t> command(cmd.begin(),cmd.end()); command.push_back(L'\0');
    STARTUPINFOW si{};si.cb=sizeof(si);PROCESS_INFORMATION pi{};
    if(!CreateProcessW(exe.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_SUSPENDED, nullptr,app.c_str(),&si,&pi)) {
        Error(L"MEGA Desktop could not start. Check package dependencies.");return 7;
    }
    HANDLE job=CreateJobObjectW(nullptr,nullptr);
    if(!job || !AssignProcessToJobObject(job,pi.hProcess)) {
        // Don't launch an untracked sync process: terminate the suspended process safely.
        TerminateProcess(pi.hProcess,1);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
        if(job)CloseHandle(job);Error(L"Cannot safely track MEGA child process. Launcher refused to start it.");return 8;
    }
    ResumeThread(pi.hThread); CloseHandle(pi.hThread);
    WaitForSingleObject(pi.hProcess,INFINITE);
    // Wait for all descendants that remain in the assigned job, including tray-related children.
    JOBOBJECT_BASIC_ACCOUNTING_INFORMATION info{};
    while(QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&info,sizeof(info),nullptr)
          && info.ActiveProcesses!=0) Sleep(500);
    DWORD code=1; GetExitCodeProcess(pi.hProcess,&code);
    CloseHandle(pi.hProcess);CloseHandle(job);
    // No host cleanup: app profile is created directly in Data; unverified shell traces remain documented.
    return static_cast<int>(code);
}
