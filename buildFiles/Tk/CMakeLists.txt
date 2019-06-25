cmake_minimum_required(VERSION 3.4.1)
project(Tk C)

add_definitions(-DHAVE_TK_CONFIG_H)
add_compile_options(--imacros=tkConfig.h)

add_library(tk SHARED
        source/generic/ttk/ttkNotebook.c source/generic/ttk/ttkProgress.c
        source/generic/ttk/ttkManager.c source/generic/ttk/ttkStubLib.c
        source/generic/ttk/ttkBlink.c source/generic/ttk/ttkSeparator.c
        source/generic/ttk/ttkButton.c source/generic/ttk/ttkCache.c
        source/generic/ttk/ttkInit.c source/generic/ttk/ttkWidget.c
        source/generic/ttk/ttkEntry.c source/generic/ttk/ttkImage.c
        source/generic/ttk/ttkTheme.c source/generic/ttk/ttkClassicTheme.c
        source/generic/ttk/ttkTreeview.c source/generic/ttk/ttkLabel.c
        source/generic/ttk/ttkState.c source/generic/ttk/ttkManager.h
        source/generic/ttk/ttkTrack.c source/generic/ttk/ttkDecls.h
        source/generic/ttk/ttkDefaultTheme.c source/generic/ttk/ttkScale.c
        source/generic/ttk/ttkLayout.c source/generic/ttk/ttkWidget.h
        source/generic/ttk/ttkClamTheme.c source/generic/ttk/ttkTheme.h
        source/generic/ttk/ttkScroll.c source/generic/ttk/ttkSquare.c
        source/generic/ttk/ttkScrollbar.c source/generic/ttk/ttkStubInit.c
        source/generic/ttk/ttkFrame.c source/generic/ttk/ttkElements.c
        source/generic/ttk/ttkTagSet.c source/generic/ttk/ttkTrace.c
        source/generic/ttk/ttkThemeInt.h source/generic/ttk/ttkPanedwindow.c
        source/generic/tkTextTag.c source/generic/tkCanvPoly.c
        source/generic/tkCanvText.c source/generic/tkMenuDraw.c
        source/generic/tkCmds.c source/generic/tkMain.c
        source/generic/tkDecls.h source/generic/tkBusy.h
        source/generic/tkGeometry.c source/generic/tkCanvLine.c
        source/generic/tkUndo.h source/generic/tkUtil.c
        source/generic/tkCanvArc.c source/generic/tkMacWinMenu.c
        source/generic/tkFileFilter.c source/generic/tkCanvPs.c
        source/generic/default.h source/generic/tkTextDisp.c
        source/generic/tkImgPhoto.c source/generic/tkImage.c
        source/generic/tkSelect.h source/generic/tkStyle.c
        source/generic/tkImgUtil.c source/generic/tkImgPPM.c
        source/generic/tkBusy.c source/generic/tkScrollbar.h
        source/generic/tkError.c source/generic/tkEntry.c
        source/generic/tkOldConfig.c source/generic/tkWindow.c
        source/generic/tkCanvas.h source/generic/tkScrollbar.c
        source/generic/tkInt.h source/generic/tkVisual.c
        source/generic/tkPack.c source/generic/tk.h
        source/generic/tkGC.c source/generic/tkFileFilter.h
        source/generic/tkImgPhInstance.c source/generic/tkCanvas.c
        source/generic/tkRectOval.c source/generic/tkText.c
        source/generic/tkScale.c source/generic/tkSelect.c
        source/generic/tkCanvWind.c source/generic/tkCanvBmap.c
        source/generic/tkTextWind.c source/generic/tkImgGIF.c
        source/generic/ks_names.h source/generic/tkEvent.c
        source/generic/tkTrig.c source/generic/tkCanvImg.c
        source/generic/tkConfig.c source/generic/tkFocus.c
        source/generic/tkGet.c source/generic/tkText.h
        source/generic/tkPlatDecls.h source/generic/tkButton.h
        source/generic/tk3d.h source/generic/tkGrab.c
        source/generic/tk3d.c source/generic/tkImgPhoto.h
        source/generic/tkBitmap.c source/generic/tkPort.h
        source/generic/tkMenubutton.c source/generic/tkIntXlibDecls.h
        source/generic/tkUndo.c source/generic/tkButton.c
        source/generic/tkFont.c source/generic/tkPanedWindow.c
        source/generic/tkPlace.c source/generic/tkBind.c
        source/generic/tkIntPlatDecls.h source/generic/tkFont.h
        source/generic/tkFrame.c source/generic/tkTextIndex.c
        source/generic/tkMessage.c source/generic/tkIntDecls.h
        source/generic/tkColor.h source/generic/tkClipboard.c
        source/generic/tkSquare.c source/generic/tkArgv.c
        source/generic/tkImgPNG.c source/generic/tkCursor.c
        source/generic/tkScale.h source/generic/tkGrid.c
        source/generic/tkEntry.h source/generic/tkOption.c
        source/generic/tkAtom.c source/generic/tkConsole.c
        source/generic/tkMenu.h source/generic/tkMenubutton.h
        source/generic/tkTextBTree.c source/generic/tkStubInit.c
        source/generic/tkStubLib.c source/generic/tkCanvUtil.c
        source/generic/tkObj.c source/generic/tkTextMark.c
        source/generic/tkListbox.c source/generic/tkTextImage.c
        source/generic/tkImgBmap.c source/generic/tkColor.c
        source/generic/tkMenu.c source/unix/tkUnixScrlbr.c
        source/unix/tkConfig.h source/unix/tkUnixKey.c
        source/unix/tkUnixWm.c source/unix/tkUnixScale.c
        source/unix/tkUnixEvent.c source/unix/tkAppInit.c
        source/unix/tkUnixDefault.h source/unix/tkUnixDraw.c
        source/unix/tkUnixEmbed.c source/unix/tkUnixCursor.c
        source/unix/tkUnix3d.c source/unix/tkUnixFocus.c
        source/unix/tkUnixMenubu.c source/unix/tkUnixColor.c
        source/unix/tkUnixXId.c source/unix/tkUnixMenu.c
        source/unix/tkUnixDialog.c source/unix/tkUnixSend.c
        source/unix/tkUnixConfig.c source/unix/tkUnix.c
        source/unix/tkUnixInit.c source/unix/tkUnixSelect.c
        source/unix/tkUnixPort.h source/unix/tkUnixButton.c
        source/unix/tkUnixInt.h source/unix/tkUnixFont.c)

target_include_directories(tk
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/generic>
        PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/unix>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/bitmaps>)

target_link_libraries(
        tk
        tcl sdl2X11Emulation)
