// Compile/link against the same Windows SDK C++/WinRT APIs as DesktopManager.
// Never execute the test: this verifies the toolchain's import library only.
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.UI.Shell.h>

int main()
{
    // Covers the activation factory path referenced in the actual failure.
    auto taskbar = winrt::try_get_activation_factory<
        winrt::Windows::UI::Shell::TaskbarManager,
        winrt::Windows::UI::Shell::ITaskbarManagerDesktopAppSupportStatics>();
    // Also cover C++/WinRT exception origination referenced in the log.
    try { winrt::check_hresult(E_FAIL); }
    catch (winrt::hresult_error const&) {}
    return taskbar ? 0 : 1;
}
