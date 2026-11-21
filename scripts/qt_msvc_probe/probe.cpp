// Reproduce the Qt 5 QList<QString>::operator== instantiation that failed
// while compiling MEGAsync's MegaIgnoreManager.cpp in b1r4.
#include <QtCore/QList>
#include <QtCore/QString>

#if !defined(_MSC_VER)
#error Only MSVC is supported by this Windows compatibility preflight.
#endif

static bool equal_qt_string_lists(const QList<QString>& a, const QList<QString>& b)
{
    return a == b; // Forces Qt's checked-array-iterator template to instantiate.
}
int main()
{
    QList<QString> first;
    QList<QString> second;
    first.append(QStringLiteral("portable"));
    second.append(QStringLiteral("portable"));
    return equal_qt_string_lists(first, second) ? 0 : 1;
}
