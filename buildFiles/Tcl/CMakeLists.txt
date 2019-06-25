cmake_minimum_required(VERSION 3.4.1)
project(Tcl C)

if (NOT DEFINED CMAKE_ANDROID_ARCH_ABI)
    message(FATAL_ERROR "Build must be a crosscompile for Android!")
endif()

if (${CMAKE_ANDROID_ARCH_ABI} STREQUAL "arm64-v8a" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "x86_64" OR
        ${CMAKE_ANDROID_ARCH_ABI} STREQUAL "mips64")
    add_definitions(-DABI_64_BIT)
else()
    add_definitions(-UABI_64_BIT)
endif()
add_definitions(
        -DHAVE_TCL_CONFIG_H -DTCL_LIBRARY="library/" -DTCL_PACKAGE_PATH="library/Tcl/"
        -DCFG_RUNTIME_LIBDIR="" -DCFG_RUNTIME_BINDIR="" -DCFG_RUNTIME_SCRDIR=""
        -DCFG_RUNTIME_INCDIR="" -DCFG_RUNTIME_DOCDIR="" -DCFG_INSTALL_LIBDIR=""
        -DCFG_INSTALL_BINDIR="" -DCFG_INSTALL_SCRDIR="" -DCFG_INSTALL_INCDIR=""
        -DCFG_INSTALL_DOCDIR="")
add_compile_options(-include stdio.h)

add_library(tcl SHARED
        source/generic/tclOOStubLib.c source/generic/tclOOBasic.c
        source/generic/tclIOUtil.c source/generic/tclIntDecls.h
        source/generic/tclClock.c source/generic/regcomp.c
        source/generic/tclObj.c source/generic/tcl.h
        source/generic/tclGet.c source/generic/tclFileSystem.h
        source/generic/tclThreadStorage.c source/generic/tclThreadJoin.c
        source/generic/tclFCmd.c source/generic/tclEnsemble.c
        source/generic/tclLiteral.c source/generic/tclFileName.c
        source/generic/tclIntPlatDecls.h source/generic/regerror.c
        source/generic/tclCompile.c source/generic/tclTomMathStubLib.c
        source/generic/tclStringObj.c source/generic/tclInt.h
        source/generic/tclNotify.c source/generic/tclCompCmdsSZ.c
        source/generic/tclVar.c source/generic/tclGetDate.y
        source/generic/tclResolve.c source/generic/tclIO.h
        source/generic/tclAsync.c source/generic/tclPkgConfig.c
        source/generic/tclOODecls.h source/generic/tclOO.h
        source/generic/tclDate.c source/generic/tclResult.c
        source/generic/tclLink.c source/generic/tclIO.c
        source/generic/tclCompCmds.c source/generic/tclEvent.c
        source/generic/tclUtil.c source/generic/tclIOCmd.c
        source/generic/tclStubLib.c source/generic/tclConfig.c
        source/generic/tclIORTrans.c source/generic/tclDisassemble.c
        source/generic/tclOOInt.h source/generic/tclCkalloc.c
        source/generic/tclHash.c source/generic/tclAssembly.c
        source/generic/tclTimer.c source/generic/tclOptimize.c
        source/generic/tclIndexObj.c source/generic/tclCmdIL.c
        source/generic/tclCmdMZ.c source/generic/tclZlib.c
        source/generic/regcustom.h source/generic/tclPreserve.c
        source/generic/tclCompExpr.c source/generic/tclTomMath.h
        source/generic/tclScan.c source/generic/tclAlloc.c
        source/generic/tclRegexp.h source/generic/tclListObj.c
        source/generic/tclIOSock.c source/generic/tclDictObj.c
        source/generic/tclDecls.h source/generic/tommath.h
        source/generic/tclTomMathInterface.c source/generic/tclOODefineCmds.c
        source/generic/tclThreadAlloc.c source/generic/tclEncoding.c
        source/generic/regfree.c source/generic/tclInterp.c
        source/generic/tclRegexp.c source/generic/tclParse.h
        source/generic/regexec.c source/generic/tclIOGT.c
        source/generic/tclStringTrim.h source/generic/tclUtf.c
        source/generic/tclNamesp.c source/generic/regex.h
        source/generic/tclPkg.c source/generic/tclPipe.c
        source/generic/tclStrToD.c source/generic/tclOOIntDecls.h
        source/generic/tclTomMathInt.h source/generic/tclExecute.c
        source/generic/tclParse.c source/generic/tclPosixStr.c
        source/generic/tclOOMethod.c source/generic/tclLoad.c
        source/generic/tclOOInfo.c source/generic/tclOO.c
        source/generic/tclStubInit.c source/generic/tclCompile.h
        source/generic/tclHistory.c source/generic/tclInt.decls
        source/generic/tclPlatDecls.h source/generic/tclPathObj.c
        source/generic/tclCompCmdsGR.c source/generic/tclThread.c
        source/generic/tclMain.c source/generic/tclBasic.c
        source/generic/tclPanic.c source/generic/tclEnv.c
        source/generic/tclCmdAH.c source/generic/tclDTrace.d
        source/generic/tclProc.c source/generic/regguts.h
        source/generic/tclBinary.c source/generic/regerrs.h
        source/generic/tclTrace.c source/generic/tclOOStubInit.c
        source/generic/tclIORChan.c source/generic/tclOOCall.c
        source/generic/tclPort.h source/generic/tclUniData.c
        source/generic/tclTomMathDecls.h source/unix/tclUnixTime.c
        source/unix/tclUnixPipe.c source/unix/tclUnixThrd.h
        source/unix/tclLoadDl.c source/unix/tclUnixFCmd.c
        source/unix/tclUnixInit.c source/unix/tclUnixEvent.c
        source/unix/tclUnixCompat.c source/unix/tclAppInit.c
        source/unix/tclUnixChan.c source/unix/tclUnixThrd.c
        source/unix/tclUnixPort.h source/unix/tclUnixFile.c
        source/unix/tclUnixSock.c source/unix/tclUnixNotfy.c
        source/unix/tclConfig.h source/libtommath/bn_fast_s_mp_mul_digs.c
        source/libtommath/bn_fast_s_mp_sqr.c source/libtommath/bn_mp_add.c
        source/libtommath/bn_mp_add_d.c source/libtommath/bn_mp_and.c
        source/libtommath/bn_mp_clamp.c source/libtommath/bn_mp_clear.c
        source/libtommath/bn_mp_clear_multi.c source/libtommath/bn_mp_cmp.c
        source/libtommath/bn_mp_cmp_d.c source/libtommath/bn_mp_cmp_mag.c
        source/libtommath/bn_mp_cnt_lsb.c source/libtommath/bn_mp_copy.c
        source/libtommath/bn_mp_count_bits.c source/libtommath/bn_mp_div.c
        source/libtommath/bn_mp_div_2.c source/libtommath/bn_mp_div_2d.c
        source/libtommath/bn_mp_div_3.c source/libtommath/bn_mp_div_d.c
        source/libtommath/bn_mp_exch.c source/libtommath/bn_mp_expt_d.c
        source/libtommath/bn_mp_grow.c source/libtommath/bn_mp_init.c
        source/libtommath/bn_mp_init_copy.c source/libtommath/bn_mp_init_multi.c
        source/libtommath/bn_mp_init_set.c source/libtommath/bn_mp_init_set_int.c
        source/libtommath/bn_mp_init_size.c source/libtommath/bn_mp_karatsuba_mul.c
        source/libtommath/bn_mp_karatsuba_sqr.c source/libtommath/bn_mp_lshd.c
        source/libtommath/bn_mp_mod.c source/libtommath/bn_mp_mod_2d.c
        source/libtommath/bn_mp_mul.c source/libtommath/bn_mp_mul_2.c
        source/libtommath/bn_mp_mul_2d.c source/libtommath/bn_mp_mul_d.c
        source/libtommath/bn_mp_neg.c source/libtommath/bn_mp_or.c
        source/libtommath/bn_mp_radix_size.c source/libtommath/bn_mp_radix_smap.c
        source/libtommath/bn_mp_read_radix.c source/libtommath/bn_mp_rshd.c
        source/libtommath/bn_mp_set.c source/libtommath/bn_mp_set_int.c
        source/libtommath/bn_mp_shrink.c source/libtommath/bn_mp_sqr.c
        source/libtommath/bn_mp_sqrt.c source/libtommath/bn_mp_sub.c
        source/libtommath/bn_mp_sub_d.c source/libtommath/bn_mp_to_unsigned_bin.c
        source/libtommath/bn_mp_to_unsigned_bin_n.c source/libtommath/bn_mp_toom_mul.c
        source/libtommath/bn_mp_toom_sqr.c source/libtommath/bn_mp_toradix_n.c
        source/libtommath/bn_mp_unsigned_bin_size.c source/libtommath/bn_mp_xor.c
        source/libtommath/bn_mp_zero.c source/libtommath/bn_reverse.c
        source/libtommath/bn_s_mp_add.c source/libtommath/bn_s_mp_mul_digs.c
        source/libtommath/bn_s_mp_sqr.c source/libtommath/bn_s_mp_sub.c
        source/libtommath/bncore.c source/libtommath/tommath.h
        source/libtommath/tommath_class.h source/libtommath/tommath_superclass.h)

target_include_directories(tcl
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/generic>
        PRIVATE
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/unix>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/source/libtommath>)

find_library(z-lib z)
target_link_libraries(
        tcl
        ${z-lib})
