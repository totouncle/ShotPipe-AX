    # ====== 고정 프로젝트 관련 메서드 추가 ======
    
    def auto_load_fixed_project(self):
        """고정 프로젝트 자동 로드"""
        try:
            if not self.shotgrid_entity_manager:
                logger.warning("Shotgrid 엔티티 매니저가 없음")
                return
                
            # 고정 프로젝트 찾기
            project = self.shotgrid_entity_manager.find_project(self.fixed_project_name)
            if project:
                # 시퀀스 목록 로드
                sequences = self.shotgrid_entity_manager.get_sequences_in_project(project)
                
                self.shotgrid_sequence_combo.clear()
                self.shotgrid_sequence_combo.addItem("-- 시퀀스 선택 --")
                
                for sequence in sequences:
                    self.shotgrid_sequence_combo.addItem(sequence['code'])
                
                # 연결 상태 업데이트
                self.shotgrid_status_label.setText("연결 상태: 연결됨")
                self.shotgrid_status_label.setStyleSheet("color: #27AE60;")
                
                logger.info(f"고정 프로젝트 '{self.fixed_project_name}' 자동 로드 완료: {len(sequences)}개 시퀀스")
                
                # 상태바 메시지 업데이트
                if hasattr(self.parent, 'status_bar'):
                    self.parent.status_bar.showMessage(f"Shotgrid 연결됨 - 프로젝트: {self.fixed_project_name}")
                    
            else:
                logger.warning(f"고정 프로젝트 '{self.fixed_project_name}'을 찾을 수 없음")
                self.shotgrid_status_label.setText("연결 상태: 프로젝트 없음")
                self.shotgrid_status_label.setStyleSheet("color: #E67E22;")
                
        except Exception as e:
            logger.error(f"고정 프로젝트 자동 로드 실패: {e}")
            self.shotgrid_status_label.setText("연결 상태: 오류")
            self.shotgrid_status_label.setStyleSheet("color: #E74C3C;")

    def on_fixed_project_sequence_changed(self, sequence_code):
        """고정 프로젝트의 시퀀스 변경 처리"""
        if not sequence_code or sequence_code == "-- 시퀀스 선택 --":
            return
            
        try:
            project = self.shotgrid_entity_manager.find_project(self.fixed_project_name)
            if not project:
                return
                
            # 샷 목록 로드
            shots = self.shotgrid_entity_manager.get_shots_in_sequence(project, sequence_code)
            
            self.shotgrid_shot_combo.clear()
            self.shotgrid_shot_combo.addItem("-- 샷 선택 --")
            
            for shot in shots:
                self.shotgrid_shot_combo.addItem(shot['code'])
                
            logger.info(f"고정 프로젝트 '{self.fixed_project_name}' 시퀀스 '{sequence_code}'에 {len(shots)}개 샷 로드됨")
            
            # 상태바 업데이트
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.showMessage(f"시퀀스: {sequence_code}, {len(shots)}개 샷 로드됨")
            
        except Exception as e:
            logger.error(f"고정 프로젝트 시퀀스 변경 처리 실패: {e}")

    def refresh_shotgrid_data(self):
        """시퀀스/샷 데이터 수동 새로고침"""
        try:
            if hasattr(self, 'auto_load_fixed_project'):
                self.auto_load_fixed_project()
                QMessageBox.information(self, "새로고침", 
                                      f"프로젝트 '{self.fixed_project_name}'의 시퀀스/샷 데이터가 새로고침되었습니다.")
            else:
                logger.warning("auto_load_fixed_project 메서드가 없음")
        except Exception as e:
            logger.error(f"Shotgrid 데이터 새로고침 실패: {e}")
            QMessageBox.warning(self, "오류", f"데이터 새로고침 중 오류가 발생했습니다: {str(e)}")

    def update_status_display(self):
        """상태 표시 업데이트"""
        try:
            # 선택된 파일 수 표시
            selected_count = 0
            for i in range(self.file_table.rowCount()):
                check_item = self.file_table.item(i, 0)
                if check_item and check_item.checkState() == Qt.Checked:
                    selected_count += 1
            
            total_count = self.file_table.rowCount()
            
            status_text = f"파일: {selected_count}/{total_count} 선택됨"
            
            # 고정 프로젝트 연결 상태
            if hasattr(self, 'shotgrid_entity_manager') and self.shotgrid_entity_manager:
                status_text += f" | 프로젝트: {self.fixed_project_name} 연결됨"
            else:
                status_text += f" | 프로젝트: 연결 안됨"
            
            # 부모 메인 윈도우의 상태바 업데이트
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.showMessage(status_text)
        except Exception as e:
            logger.error(f"상태 표시 업데이트 실패: {e}")

    def save_ui_settings(self):
        """UI 설정 저장"""
        try:
            settings = {
                "fixed_project": self.fixed_project_name,
                "last_sequence": self.shotgrid_sequence_combo.currentText() if hasattr(self, 'shotgrid_sequence_combo') else "",
                "last_shot": self.shotgrid_shot_combo.currentText() if hasattr(self, 'shotgrid_shot_combo') else "",
                "table_column_widths": [
                    self.file_table.columnWidth(i) 
                    for i in range(self.file_table.columnCount())
                ]
            }
            
            settings_file = os.path.expanduser("~/.shotpipe/ui_settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            logger.debug("UI 설정 저장 완료")
        except Exception as e:
            logger.error(f"UI 설정 저장 실패: {e}")

    def load_ui_settings(self):
        """UI 설정 로드"""
        try:
            settings_file = os.path.expanduser("~/.shotpipe/ui_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                # 테이블 열 너비 복원
                if "table_column_widths" in settings:
                    for i, width in enumerate(settings["table_column_widths"]):
                        if i < self.file_table.columnCount():
                            self.file_table.setColumnWidth(i, width)
                
                # 마지막 선택된 시퀀스/샷 복원
                if hasattr(self, 'shotgrid_sequence_combo') and "last_sequence" in settings:
                    index = self.shotgrid_sequence_combo.findText(settings["last_sequence"])
                    if index >= 0:
                        self.shotgrid_sequence_combo.setCurrentIndex(index)
                        
                logger.debug("UI 설정 로드 완료")
                        
        except Exception as e:
            logger.error(f"UI 설정 로드 실패: {e}")

    def closeEvent(self, event):
        """위젯 종료 시 설정 저장"""
        try:
            self.save_ui_settings()
            event.accept()
        except Exception as e:
            logger.error(f"종료 시 설정 저장 실패: {e}")
            event.accept()
    
    def _assign_task_automatically(self, file_path):
        """파일 유형에 따라 자동으로 태스크 할당"""
        try:
            # 파일 확장자 추출
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # AI 서비스 태스크 매핑 표에 따른 자동 할당
            if ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.gif', '.bmp', '.webp', '.exr', '.dpx']:
                return 'txtToImage'  # 이미지 파일은 Text to Image 태스크
            elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.mxf', '.m4v', '.webm']:
                return 'imgToVideo'  # 비디오 파일은 Image to Video 태스크
            else:
                return 'comp'  # 기본 태스크
                
        except Exception as e:
            logger.error(f"자동 태스크 할당 실패: {e}")
            return 'comp'  # 오류 시 기본 태스크 반환
