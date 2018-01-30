#include <QObject>
#include <QWidget>
#include <QKeyEvent>
#include <QLabel>
#include <QSoundEffect>

class Win : public QWidget
{
    Q_OBJECT

  public:
    Win(QWidget* parent = Q_NULLPTR);
    ~Win();
    
    virtual void keyPressEvent(QKeyEvent *event);
    virtual void keyReleaseEvent(QKeyEvent *event);

  private:
    QLabel* escWidget;
    QLabel* downWidget;
    QLabel* upWidget;
    QLabel* enterWidget;
    QSoundEffect* escSfx;
    QSoundEffect* downSfx;
    QSoundEffect* upSfx;
    QSoundEffect* enterSfx;
};

