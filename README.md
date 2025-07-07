# Blender Scripting with Python  

WIP ( Work in Progress ).  
블렌더를 위한 애드온 개발을 위해서 생성 하였습니다.  

- VS Code의 명령창(Ctrl+Shift+P)에서 'Blender: Run Script'로 실행시에는 __name__ 이 "<run_path>" 로 설정되어 코드 수정 필요 ...  
- ...  



## 책 관련 링크

<img src="979-8-8688-1126-5.jpg" alt="" height="256px" align="right">

- [Blender Script with Python [ 원서 ]](https://link.springer.com/book/10.1007/979-8-8688-1127-2)  

- [Source Code](https://github.com/Apress/Blender-Scripting-with-Python)  


## 개발 및 테스트 환경

- 시스템 ( Computer System )  

  - AMD Ryzen 9 5900X 12-Core Processor
  - 32G RAM
  - NVIDIA Geforce RTX 3080 10GB
  - SSD 2TB
  - Windows 11 64bit Korean

- 블렌더 ( Blender 4.4.3 )  

  - [Blender Download](https://www.blender.org/download/)  
    - [v4.4.3 for Windows](https://download.blender.org/release/Blender4.4/blender-4.4.3-windows-x64.msi)  
    - [v4.4.0 for Windows](https://download.blender.org/release/Blender4.4/blender-4.4.0-windows-x64.msi)  
    - 내장된 파이썬 버전은 Python v3.11.11 입니다.  

- 파이썬 ( Python 3.12 )  

  - [Python Download](https://www.python.org/downloads/)  
    - [v3.12.0 for Windows](https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe)  
    - [v3.11.9 for Windows](https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe)  

- 에디터 ( Editor, Intergrated Development Environment )  

  - [VS Code](https://visualstudio.microsoft.com/ko/free-developer-offers/)  
    - [Python Extension for VS Code](https://marketplace.visualstudio.com/items?itemName=ms-python.python)  
      - Python Interpreter Chooser  
      - Pylance  
      - Python Debugger  
      -  
    - [Blender Development](https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development)  
      - Blender: Start  
      - Blender: Stop  
      - Blender: Run Script  
      -  

- 패키지 매니저 ( Package Manager )
  - [pypi](https://pypi.org/)  
    - [검색](https://pypi.org/search/)  
    - ...
    ```
    $ pip --version
    $ pip --help
    ```
    ```
    $ pip install fake-bpy-module-latest
    $ pip list
    ```
    ```
    $ pip freeze >> requirements.txt
    $ pip install -r ./requirements.txt
    ```


## 사용된 패키지 목록

- fake-bpy-module
  - [pypi](https://pypi.org/project/fake-bpy-module/)  
    ```
    $ pip install fake-bpy-module-latest
    ```
  - [fake-bpy-module](https://github.com/nutti/fake-bpy-module)  
  - Fake Blender Python API module collection

- ...
  - [pypi]()  
  ```
  $ vcpkg add port ...
  ```
  - [...]()
  - ...  


## ...

---  
---  
---  


# Apress Source Code

This repository accompanies [*Blender Scripting with Python*](https://link.springer.com/book/979-8-8688-1127-2) by Isabel Lupiani (Apress, 2025).

[comment]: #cover
![Cover image](979-8-8688-1126-5.jpg)

Download the files as a zip using the green button, or clone the repository to your machine using Git.

## Releases

Release v1.0 corresponds to the code and figures in the published book, without corrections or updates.

## Contributions

See the file Contributing.md for more information on how you can contribute to this repository.
