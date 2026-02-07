#include <windows.h>
#include <commctrl.h>
#include <thread>
#include <string>

#pragma comment(lib, "comctl32.lib")

#define IDI_MAINICON 101

const char g_szClassName[] = "LoaderWindow";
HWND g_hProgressBar = NULL;

// Cambia esto por tu ejecutable
LPCSTR RUTA_APP = "appdata/TucanMax.exe";

// Cambia este título por la ventana de tu app real
LPCSTR TITULO_APP = "TUCAN MAX";

// --------------------------------
// Procedimiento de la ventana
// --------------------------------
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    switch (msg)
    {
        case WM_CLOSE:
            DestroyWindow(hwnd);
            break;

        case WM_DESTROY:
            PostQuitMessage(0);
            break;

        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

// --------------------------------
// Hilo secundario que lanza la app
// --------------------------------
void lanzarYMonitorear(HWND hwndLoader)
{
    STARTUPINFO si = { sizeof(STARTUPINFO) };
    PROCESS_INFORMATION pi;

    BOOL res = CreateProcess(
        RUTA_APP, 
        NULL, NULL, NULL,
        FALSE, 0,
        NULL, NULL,
        &si, &pi
    );

    if (!res)
    {
        MessageBox(hwndLoader, "No se pudo ejecutar la app principal.", "Error", MB_OK | MB_ICONERROR);
        PostMessage(hwndLoader, WM_CLOSE, 0, 0);
        return;
    }

    // ----------------------------
    // MONITOREO DEL INICIO DE APP
    // ----------------------------
    int progreso = 0;
    for (;;)
    {
        // Actualizar barra de progreso
        if (g_hProgressBar != NULL)
        {
            progreso = (progreso + 5) % 100;
            SendMessage(g_hProgressBar, PBM_SETPOS, progreso, 0);
        }

        // Ver si la ventana de la app existe
        HWND win = FindWindow(NULL, TITULO_APP);

        if (win != NULL)
        {
            // La app ya inició → cerrar pantalla de carga
            PostMessage(hwndLoader, WM_CLOSE, 0, 0);
            return;
        }

        // Si el proceso terminó antes de abrir la ventana → cerrar loader
        DWORD result;
        GetExitCodeProcess(pi.hProcess, &result);

        if (result != STILL_ACTIVE)
        {
            PostMessage(hwndLoader, WM_CLOSE, 0, 0);
            return;
        }

        Sleep(100); // comprobar cada 100ms
    }
}

// --------------------------------
// WinMain
//---------------------------------
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int nCmdShow)
{
    // Inicializar controles comunes
    INITCOMMONCONTROLSEX icc;
    icc.dwSize = sizeof(INITCOMMONCONTROLSEX);
    icc.dwICC = ICC_PROGRESS_CLASS;
    InitCommonControlsEx(&icc);

    WNDCLASSEX wc = { sizeof(WNDCLASSEX) };
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.lpszClassName = g_szClassName;
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    wc.hIcon = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_MAINICON));
    wc.hIconSm = LoadIcon(hInstance, MAKEINTRESOURCE(IDI_MAINICON));

    RegisterClassEx(&wc);

    // Dimensiones de la ventana
    int ancho = 400;
    int alto = 150;

    // Obtener dimensiones de la pantalla para centrar
    int screenX = GetSystemMetrics(SM_CXSCREEN);
    int screenY = GetSystemMetrics(SM_CYSCREEN);
    int posX = (screenX - ancho) / 2;
    int posY = (screenY - alto) / 2;

    // Ventana del loader centrada
    HWND hwnd = CreateWindowEx(
        WS_EX_TOPMOST,
        g_szClassName,
        "TucanMax se esta iniciando...",
        WS_POPUP | WS_BORDER | WS_CAPTION,
        posX, posY,
        ancho, alto,
        NULL, NULL, hInstance, NULL
    );

    // Texto arriba de la barra
    CreateWindow(
        "STATIC",
        "Tucan Max se esta iniciando\nPor favor espere...",
        WS_VISIBLE | WS_CHILD | SS_CENTER,
        20, 20, ancho - 40, 40,
        hwnd, NULL, hInstance, NULL
    );

    // Barra de progreso
    g_hProgressBar = CreateWindowEx(
        0,
        PROGRESS_CLASS,
        NULL,
        WS_VISIBLE | WS_CHILD | PBS_SMOOTH,
        40, 75, ancho - 80, 25,
        hwnd, NULL, hInstance, NULL
    );

    // Configurar rango de la barra
    SendMessage(g_hProgressBar, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
    SendMessage(g_hProgressBar, PBM_SETSTEP, 1, 0);

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    // Lanzar hilo para ejecutar app y monitorearla
    std::thread hilo(lanzarYMonitorear, hwnd);
    hilo.detach();

    // Loop de mensajes
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0) > 0)
    {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    return 0;
}
